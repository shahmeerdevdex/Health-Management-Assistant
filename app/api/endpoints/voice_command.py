from fastapi import APIRouter, UploadFile, File, Depends, Response, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.voice_services import transcribe_audio, generate_speech
from app.api.endpoints.dependencies import get_db, get_current_user
from app.schemas.voice_command import (
    VoiceCommandResponse,
    VoiceCommandRequest,
    VoiceCommandType,
    VoiceCommandResult
)
from app.services.command_processor import process_voice_command
from app.db.models.user import User
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/command", response_model=VoiceCommandResponse)
async def process_voice_command_endpoint(
    audio: UploadFile = File(...),
    command_type: VoiceCommandType = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Process voice commands with the following capabilities:
    - Health logging (symptoms, medications, mood)
    - Appointment scheduling
    - Emergency alerts
    - Navigation commands
    - Information requests
    """
    try:
        # Read audio file
        audio_bytes = await audio.read()
        
        # Transcribe audio to text
        text_command = await transcribe_audio(audio_bytes)
        
        # Process the command
        result = await process_voice_command(
            db=db,
            user_id=current_user.id,
            command_text=text_command,
            command_type=command_type
        )
        
        # Generate voice response if needed
        voice_response = None
        if result.requires_voice_response:
            voice_response = await generate_speech(
                text=result.response_text,
                voice_name=current_user.accessibility_preferences.preferred_voice if current_user.accessibility_preferences else "Rachel"
            )
        
        return VoiceCommandResponse(
            command_type=result.command_type,
            recognized_text=text_command,
            response_text=result.response_text,
            success=result.success,
            action_taken=result.action_taken,
            voice_response=voice_response
        )
        
    except Exception as e:
        logger.error(f"Voice command processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/available-commands")
async def get_available_commands(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of available voice commands and their descriptions.
    """
    return {
        "health_logging": {
            "log_symptom": "Log a new symptom (e.g., 'Log symptom headache')",
            "log_medication": "Log medication taken (e.g., 'Log medication aspirin')",
            "log_mood": "Log current mood (e.g., 'Log mood happy')",
            "log_vitals": "Log vital signs (e.g., 'Log vitals blood pressure 120/80')"
        },
        "appointments": {
            "schedule_appointment": "Schedule a new appointment (e.g., 'Schedule appointment with Dr. Smith')",
            "check_appointments": "Check upcoming appointments (e.g., 'Show my appointments')",
            "reschedule_appointment": "Reschedule an appointment (e.g., 'Reschedule my next appointment')"
        },
        "emergency": {
            "emergency_alert": "Trigger emergency alert (e.g., 'Emergency help needed')",
            "emergency_contact": "Call emergency contact (e.g., 'Call emergency contact')"
        },
        "navigation": {
            "find_doctor": "Find nearby doctors (e.g., 'Find doctor near me')",
            "find_pharmacy": "Find nearby pharmacies (e.g., 'Find pharmacy')",
            "find_hospital": "Find nearby hospitals (e.g., 'Find hospital')"
        },
        "information": {
            "check_medications": "Check medication schedule (e.g., 'Show my medications')",
            "check_health_summary": "Get health summary (e.g., 'Show health summary')",
            "check_care_plan": "View care plan (e.g., 'Show care plan')"
        }
    }

@router.post("/test-command")
async def test_voice_command(
    command: VoiceCommandRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Test voice command processing with text input (for development and testing).
    """
    try:
        result = await process_voice_command(
            db=db,
            user_id=current_user.id,
            command_text=command.command_text,
            command_type=command.command_type
        )
        
        return VoiceCommandResult(
            command_type=result.command_type,
            response_text=result.response_text,
            success=result.success,
            action_taken=result.action_taken
        )
        
    except Exception as e:
        logger.error(f"Voice command test error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
