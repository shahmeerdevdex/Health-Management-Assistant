from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.voice_command import VoiceCommandType, VoiceCommandResult
from app.crud.health_diary import create_health_diary
from app.schemas.health_diary import HealthDiaryCreate
from app.crud.appointment import create_appointment, get_upcoming_appointments
from app.crud.emergency_health import create_emergency_alert
from app.services.locate_health_services import get_nearby_health_services
from app.crud.medication import get_user_medications
from app.crud.health_diary import get_health_summary
from app.services.care_plan_service import get_care_plan_summary
import logging
import re
from typing import Dict, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class CommandProcessor:
    def __init__(self):
        self.command_patterns = {
            VoiceCommandType.HEALTH_LOGGING: {
                "log_symptom": r"log symptom (\w+)",
                "log_medication": r"log medication (\w+)",
                "log_mood": r"log mood (\d+)",
                "log_vitals": r"log vitals (.+)"
            },
            VoiceCommandType.APPOINTMENT: {
                "schedule": r"schedule appointment with (.+)",
                "check": r"show my appointments",
                "reschedule": r"reschedule my next appointment"
            },
            VoiceCommandType.EMERGENCY: {
                "alert": r"emergency help needed",
                "contact": r"call emergency contact"
            },
            VoiceCommandType.NAVIGATION: {
                "doctor": r"find doctor near me",
                "pharmacy": r"find pharmacy",
                "hospital": r"find hospital"
            },
            VoiceCommandType.INFORMATION: {
                "medications": r"show my medications",
                "health_summary": r"show health summary",
                "care_plan": r"show care plan"
            }
        }

    async def process_command(
        self,
        db: AsyncSession,
        user_id: int,
        command_text: str,
        command_type: Optional[VoiceCommandType] = None
    ) -> VoiceCommandResult:
        """
        Process a voice command and return the result.
        """
        try:
            #If command type is not specified, try to detect it
            if not command_type:
                command_type = self._detect_command_type(command_text)
            
             #Process based on command type
            if command_type == VoiceCommandType.HEALTH_LOGGING:
                return await self._process_health_logging(db, user_id, command_text)
            elif command_type == VoiceCommandType.APPOINTMENT:
                return await self._process_appointment(db, user_id, command_text)
            elif command_type == VoiceCommandType.EMERGENCY:
                return await self._process_emergency(db, user_id, command_text)
            elif command_type == VoiceCommandType.NAVIGATION:
                return await self._process_navigation(db, user_id, command_text)
            elif command_type == VoiceCommandType.INFORMATION:
                return await self._process_information(db, user_id, command_text)
            else:
                return VoiceCommandResult(
                    command_type=command_type,
                    response_text="I'm sorry, I couldn't understand that command.",
                    success=False,
                    action_taken="none"
                )
                
        except Exception as e:
            logger.error(f"Error processing command: {str(e)}")
            return VoiceCommandResult(
                command_type=command_type or VoiceCommandType.INFORMATION,
                response_text="An error occurred while processing your command.",
                success=False,
                action_taken="error"
            )

    def _detect_command_type(self, command_text: str) -> VoiceCommandType:
        """
        Detect the type of command from the text.
        """
        for cmd_type, patterns in self.command_patterns.items():
            for pattern in patterns.values():
                if re.search(pattern, command_text.lower()):
                    return cmd_type
        return VoiceCommandType.INFORMATION

    async def _process_health_logging(
        self,
        db: AsyncSession,
        user_id: int,
        command_text: str
    ) -> VoiceCommandResult:
        """
        Process health logging commands.
        """
        for action, pattern in self.command_patterns[VoiceCommandType.HEALTH_LOGGING].items():
            match = re.search(pattern, command_text.lower())
            if match:
                if action == "log_symptom":
                    symptom = match.group(1)
                    diary_entry = HealthDiaryCreate(
                        user_id=user_id,
                        symptoms=[symptom],
                        mood=3,  # Default mood
                        notes=f"Logged symptom: {symptom}",
                        date=datetime.now(timezone.utc)
                    )
                    await create_health_diary(db, diary_entry)
                    return VoiceCommandResult(
                        command_type=VoiceCommandType.HEALTH_LOGGING,
                        response_text=f"Logged symptom: {symptom}",
                        success=True,
                        action_taken="log_symptom"
                    )
                elif action == "log_medication":
                    medication = match.group(1)
                    diary_entry = HealthDiaryCreate(
                        user_id=user_id,
                        symptoms=[],
                        mood=3,  # Default mood
                        notes=f"Logged medication: {medication}",
                        date=datetime.now(timezone.utc)
                    )
                    await create_health_diary(db, diary_entry)
                    return VoiceCommandResult(
                        command_type=VoiceCommandType.HEALTH_LOGGING,
                        response_text=f"Logged medication: {medication}",
                        success=True,
                        action_taken="log_medication"
                    )
                elif action == "log_mood":
                    mood = int(match.group(1))
                    diary_entry = HealthDiaryCreate(
                        user_id=user_id,
                        symptoms=[],
                        mood=mood,
                        notes=f"Logged mood: {mood}",
                        date=datetime.now(timezone.utc)
                    )
                    await create_health_diary(db, diary_entry)
                    return VoiceCommandResult(
                        command_type=VoiceCommandType.HEALTH_LOGGING,
                        response_text=f"Logged mood: {mood}",
                        success=True,
                        action_taken="log_mood"
                    )
                elif action == "log_vitals":
                    vitals = match.group(1)
                    diary_entry = HealthDiaryCreate(
                        user_id=user_id,
                        symptoms=[],
                        mood=3,  # Default mood
                        notes=f"Logged vitals: {vitals}",
                        date=datetime.now(timezone.utc)
                    )
                    await create_health_diary(db, diary_entry)
                    return VoiceCommandResult(
                        command_type=VoiceCommandType.HEALTH_LOGGING,
                        response_text=f"Logged vitals: {vitals}",
                        success=True,
                        action_taken="log_vitals"
                    )

        return VoiceCommandResult(
            command_type=VoiceCommandType.HEALTH_LOGGING,
            response_text="I couldn't understand the health logging command.",
            success=False,
            action_taken="none"
        )

    async def _process_appointment(
        self,
        db: AsyncSession,
        user_id: int,
        command_text: str
    ) -> VoiceCommandResult:
        """
        Process appointment-related commands.
        """
        for action, pattern in self.command_patterns[VoiceCommandType.APPOINTMENT].items():
            match = re.search(pattern, command_text.lower())
            if match:
                if action == "schedule":
                    doctor = match.group(1)
                    # Implement appointment scheduling logic
                    return VoiceCommandResult(
                        command_type=VoiceCommandType.APPOINTMENT,
                        response_text=f"Scheduling appointment with {doctor}",
                        success=True,
                        action_taken="schedule_appointment"
                    )
                elif action == "check":
                    appointments = await get_upcoming_appointments(db, user_id)
                    return VoiceCommandResult(
                        command_type=VoiceCommandType.APPOINTMENT,
                        response_text=f"You have {len(appointments)} upcoming appointments",
                        success=True,
                        action_taken="check_appointments"
                    )
                # Add other appointment actions...

        return VoiceCommandResult(
            command_type=VoiceCommandType.APPOINTMENT,
            response_text="I couldn't understand the appointment command.",
            success=False,
            action_taken="none"
        )

    async def _process_emergency(
        self,
        db: AsyncSession,
        user_id: int,
        command_text: str
    ) -> VoiceCommandResult:
        """
        Process emergency-related commands.
        """
        for action, pattern in self.command_patterns[VoiceCommandType.EMERGENCY].items():
            if re.search(pattern, command_text.lower()):
                if action == "alert":
                    await create_emergency_alert(db, user_id, "voice_command")
                    return VoiceCommandResult(
                        command_type=VoiceCommandType.EMERGENCY,
                        response_text="Emergency alert has been sent. Help is on the way.",
                        success=True,
                        action_taken="emergency_alert"
                    )
                # Add other emergency actions...

        return VoiceCommandResult(
            command_type=VoiceCommandType.EMERGENCY,
            response_text="I couldn't understand the emergency command.",
            success=False,
            action_taken="none"
        )

    async def _process_navigation(
        self,
        db: AsyncSession,
        user_id: int,
        command_text: str
    ) -> VoiceCommandResult:
        """
        Process navigation-related commands.
        """
        for action, pattern in self.command_patterns[VoiceCommandType.NAVIGATION].items():
            if re.search(pattern, command_text.lower()):
                if action == "doctor":
                    locations = await get_nearby_health_services(db, user_id, "doctor")
                    return VoiceCommandResult(
                        command_type=VoiceCommandType.NAVIGATION,
                        response_text="Doctor location functionality is temporarily disabled.",
                        success=False,
                        action_taken="none"
                    )
                if action == "pharmacy":
                    locations = await get_nearby_health_services(db, user_id, "pharmacy")
                    return VoiceCommandResult(
                        command_type=VoiceCommandType.NAVIGATION,
                        response_text="Pharmacy location functionality is temporarily disabled.",
                        success=False,
                        action_taken="none"
                    )
                if action == "hospital":
                    locations = await get_nearby_health_services(db, user_id, "hospital")
                    return VoiceCommandResult(
                        command_type=VoiceCommandType.NAVIGATION,
                        response_text="Hospital location functionality is temporarily disabled.",
                        success=False,
                        action_taken="none"
                    )
                # Add other navigation actions...

        return VoiceCommandResult(
            command_type=VoiceCommandType.NAVIGATION,
            response_text="I couldn't understand the navigation command.",
            success=False,
            action_taken="none"
        )

    async def _process_information(
        self,
        db: AsyncSession,
        user_id: int,
        command_text: str
    ) -> VoiceCommandResult:
        """
        Process information-related commands.
        """
        for action, pattern in self.command_patterns[VoiceCommandType.INFORMATION].items():
            if re.search(pattern, command_text.lower()):
                if action == "medications":
                    medications = await get_user_medications(db, user_id)
                    return VoiceCommandResult(
                        command_type=VoiceCommandType.INFORMATION,
                        response_text=f"You have {len(medications)} active medications",
                        success=True,
                        action_taken="check_medications"
                    )
                elif action == "health_summary":
                    summary = await get_health_summary(db, user_id)
                    return VoiceCommandResult(
                        command_type=VoiceCommandType.INFORMATION,
                        response_text="Here's your health summary",
                        success=True,
                        action_taken="check_health_summary",
                        meta_data={"summary": summary}
                    )
                # Add other information actions...

        return VoiceCommandResult(
            command_type=VoiceCommandType.INFORMATION,
            response_text="I couldn't understand the information command.",
            success=False,
            action_taken="none"
        )

# Create a singleton instance
command_processor = CommandProcessor()

async def process_voice_command(
    db: AsyncSession,
    user_id: int,
    command_text: str,
    command_type: Optional[VoiceCommandType] = None
) -> VoiceCommandResult:
    """
    Process a voice command using the command processor.
    """
    return await command_processor.process_command(db, user_id, command_text, command_type) 