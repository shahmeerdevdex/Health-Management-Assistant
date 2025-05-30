from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.api.endpoints.dependencies import get_db, get_current_user
from app.schemas.accessibility import (
    UserAccessibilityCreate,
    UserAccessibilityUpdate,
    UserAccessibilityResponse,
    AccessibilityLogResponse,
    VoiceCommandResponse
)
from app.services.accessibility_service import (
    create_user_accessibility,
    get_user_accessibility,
    update_user_accessibility,
    log_accessibility_usage,
    get_accessibility_logs,
    process_voice_input,
    generate_voice_output
)
from app.db.models.user import User

router = APIRouter()

@router.post("/preferences", response_model=UserAccessibilityResponse)
async def create_accessibility_preferences(
    preferences: UserAccessibilityCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create or update user accessibility preferences."""
    return await create_user_accessibility(db, preferences)

@router.get("/preferences", response_model=UserAccessibilityResponse)
async def get_accessibility_preferences(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user accessibility preferences."""
    preferences = await get_user_accessibility(db, current_user.id)
    if not preferences:
        raise HTTPException(status_code=404, detail="Accessibility preferences not found")
    return preferences

@router.put("/preferences", response_model=UserAccessibilityResponse)
async def update_accessibility_preferences(
    preferences: UserAccessibilityUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update user accessibility preferences."""
    updated = await update_user_accessibility(db, preferences, current_user.id)
    if not updated:
        raise HTTPException(status_code=404, detail="Accessibility preferences not found")
    return updated

@router.get("/logs", response_model=List[AccessibilityLogResponse])
async def get_logs(
    feature: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get accessibility usage logs."""
    return await get_accessibility_logs(
        db,
        current_user.id,
        feature,
        start_date,
        end_date
    )

@router.post("/voice/input", response_model=VoiceCommandResponse)
async def process_voice(
    audio: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Process voice input and execute commands."""
    try:
        # Validate file type
        if not audio.content_type.startswith('audio/'):
            raise HTTPException(
                status_code=400,
                detail="Invalid file type. Only audio files are accepted."
            )

        # Read the audio file
        audio_bytes = await audio.read()
        
        # Process the voice input
        result = await process_voice_input(
            audio_bytes,
            current_user.id,
            db
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/voice/output")
async def generate_voice(
    text: str,
    voice_name: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate voice output from text."""
    try:
        audio_bytes = await generate_voice_output(text, voice_name)
        return {
            "audio": audio_bytes,
            "content_type": "audio/mpeg"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
