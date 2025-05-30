from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.accessibility import UserAccessibility, AccessibilityLog
from app.schemas.accessibility import (
    UserAccessibilityCreate,
    UserAccessibilityUpdate,
    AccessibilityLogCreate
)
from app.services.voice_services import transcribe_audio, generate_speech
from openai import OpenAI
from app.core.config import settings
import logging
import json
import io
from pydub import AudioSegment
import tempfile
import os

logger = logging.getLogger(__name__)

# Initialize OpenAI client
openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)

# Add voice command configuration
VOICE_COMMANDS = {
    "navigation": {
        "patterns": [
            "go to {page}",
            "navigate to {page}",
            "open {page}",
            "show {page}"
        ],
        "pages": ["home", "profile", "settings", "medical records", "appointments", "medications"]
    },
    "actions": {
        "patterns": [
            "schedule {action}",
            "book {action}",
            "make {action}",
            "create {action}"
        ],
        "actions": ["appointment", "reminder", "note", "prescription"]
    },
    "queries": {
        "patterns": [
            "show me {query}",
            "what is {query}",
            "tell me about {query}",
            "get {query}"
        ],
        "queries": ["medications", "allergies", "conditions", "history"]
    }
}

async def create_user_accessibility(
    db: AsyncSession,
    accessibility_data: UserAccessibilityCreate
) -> UserAccessibility:
    """Create or update user accessibility preferences."""
    # Check if preferences already exist
    query = select(UserAccessibility).where(UserAccessibility.user_id == accessibility_data.user_id)
    result = await db.execute(query)
    existing = result.scalar_one_or_none()

    if existing:
        # Update existing preferences
        for key, value in accessibility_data.dict(exclude_unset=True).items():
            setattr(existing, key, value)
        existing.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(existing)
        return existing
    else:
        # Create new preferences
        now = datetime.utcnow()
        accessibility = UserAccessibility(
            **accessibility_data.dict(),
            created_at=now,
            updated_at=now
        )
        db.add(accessibility)
        await db.commit()
        await db.refresh(accessibility)
        return accessibility

async def get_user_accessibility(
    db: AsyncSession,
    user_id: int
) -> Optional[UserAccessibility]:
    """Get user accessibility preferences."""
    query = select(UserAccessibility).where(UserAccessibility.user_id == user_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def update_user_accessibility(
    db: AsyncSession,
    update_data: UserAccessibilityUpdate,
    user_id: int
) -> Optional[UserAccessibility]:
    """Update existing user accessibility preferences."""
    query = select(UserAccessibility).where(UserAccessibility.user_id == user_id)
    result = await db.execute(query)
    existing = result.scalar_one_or_none()

    if not existing:
        return None

    # Get the update data as dict, excluding unset values
    update_dict = update_data.dict(exclude_unset=True)
    
    # Ensure voice_speed and text_size are within valid range if they are being updated
    if 'voice_speed' in update_dict:
        update_dict['voice_speed'] = max(1, min(5, update_dict['voice_speed']))
    if 'text_size' in update_dict:
        update_dict['text_size'] = max(1, min(5, update_dict['text_size']))

    # Update the fields
    for key, value in update_dict.items():
        setattr(existing, key, value)

    existing.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(existing)
    return existing

async def log_accessibility_usage(
    db: AsyncSession,
    log_data: AccessibilityLogCreate
) -> AccessibilityLog:
    """Log accessibility feature usage."""
    log = AccessibilityLog(**log_data.dict())
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return log

async def get_accessibility_logs(
    db: AsyncSession,
    user_id: int,
    feature: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> List[AccessibilityLog]:
    """Get accessibility usage logs with optional filters."""
    query = select(AccessibilityLog).where(AccessibilityLog.user_id == user_id)
    
    if feature:
        query = query.where(AccessibilityLog.feature_used == feature)
    if start_date:
        query = query.where(AccessibilityLog.created_at >= start_date)
    if end_date:
        query = query.where(AccessibilityLog.created_at <= end_date)
    
    result = await db.execute(query)
    return result.scalars().all()

async def process_voice_command(
    text: str,
    user_id: int,
    db: AsyncSession
) -> Dict[str, Any]:
    """Process voice command with NLP and context awareness."""
    try:
        # Use OpenAI to understand the command
        response = await openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": """You are a voice command processor for a healthcare application.
                    Analyze the command and extract the intent and parameters.
                    Return a JSON with:
                    - intent: navigation, action, query, or unknown
                    - parameters: extracted parameters
                    - confidence: confidence score (0-1)
                    - suggested_commands: list of related commands"""
                },
                {
                    "role": "user",
                    "content": text
                }
            ],
            temperature=0.3
        )

        command_analysis = json.loads(response.choices[0].message.content)

        # Process the command based on intent
        result = await _execute_command(command_analysis, user_id, db)

        # Log the command
        await log_accessibility_usage(
            db,
            AccessibilityLogCreate(
                user_id=user_id,
                feature_used="voice_command",
                success=True,
                meta_data={
                    "command": text,
                    "intent": command_analysis["intent"],
                    "confidence": command_analysis["confidence"]
                }
            )
        )

        return {
            "command": text,
            "analysis": command_analysis,
            "result": result,
            "suggested_commands": command_analysis.get("suggested_commands", [])
        }

    except Exception as e:
        logger.error(f"Voice command processing error: {str(e)}")
        raise

async def _execute_command(
    analysis: Dict[str, Any],
    user_id: int,
    db: AsyncSession
) -> Dict[str, Any]:
    """Execute the analyzed command."""
    intent = analysis["intent"]
    parameters = analysis.get("parameters", {})

    if intent == "navigation":
        return await _handle_navigation(parameters, user_id, db)
    elif intent == "action":
        return await _handle_action(parameters, user_id, db)
    elif intent == "query":
        return await _handle_query(parameters, user_id, db)
    else:
        return {
            "status": "unknown_command",
            "message": "I couldn't understand that command. Please try again."
        }

async def _handle_navigation(
    parameters: Dict[str, Any],
    user_id: int,
    db: AsyncSession
) -> Dict[str, Any]:
    """Handle navigation commands."""
    page = parameters.get("page", "").lower()
    if page in VOICE_COMMANDS["navigation"]["pages"]:
        return {
            "status": "success",
            "action": "navigate",
            "page": page
        }
    return {
        "status": "error",
        "message": f"Unknown page: {page}"
    }

async def _handle_action(
    parameters: Dict[str, Any],
    user_id: int,
    db: AsyncSession
) -> Dict[str, Any]:
    """Handle action commands."""
    action = parameters.get("action", "").lower()
    if action in VOICE_COMMANDS["actions"]["actions"]:
        return {
            "status": "success",
            "action": action,
            "parameters": parameters
        }
    return {
        "status": "error",
        "message": f"Unknown action: {action}"
    }

async def _handle_query(
    parameters: Dict[str, Any],
    user_id: int,
    db: AsyncSession
) -> Dict[str, Any]:
    """Handle query commands."""
    query = parameters.get("query", "").lower()
    if query in VOICE_COMMANDS["queries"]["queries"]:
        return {
            "status": "success",
            "action": "query",
            "query": query,
            "parameters": parameters
        }
    return {
        "status": "error",
        "message": f"Unknown query: {query}"
    }

async def process_voice_input(
    audio_bytes: bytes,
    user_id: Optional[int] = None,
    db: Optional[AsyncSession] = None
) -> Dict:
    """Process voice input with command recognition."""
    try:
        # Convert audio to a supported format (WAV)
        audio = AudioSegment.from_file(io.BytesIO(audio_bytes))
        
        # Create a temporary file for the converted audio
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            audio.export(temp_file.name, format='wav')
            temp_file_path = temp_file.name

        try:
            # Read the converted audio file
            with open(temp_file_path, 'rb') as f:
                converted_audio_bytes = f.read()

            # Transcribe the audio
            text = await transcribe_audio(converted_audio_bytes)
            
            # Process as voice command if user_id and db are provided
            if user_id and db:
                command_result = await process_voice_command(text, user_id, db)
                return {
                    "original_text": text,
                    "command_result": command_result
                }
            
            return {
                "text": text
            }
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    except Exception as e:
        logger.error(f"Voice input processing error: {str(e)}")
        raise

async def generate_voice_output(
    text: str,
    voice_name: Optional[str] = None
) -> bytes:
    """Generate voice output."""
    try:
        # Generate speech
        return await generate_speech(text, voice_name or "Rachel")
    except Exception as e:
        logger.error(f"Voice output generation error: {str(e)}")
        raise 