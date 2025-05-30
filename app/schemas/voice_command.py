from pydantic import BaseModel
from typing import Optional
from enum import Enum

class VoiceCommandResponse(BaseModel):
    command: str
    result: Optional[str] = None
    success: bool = True
    message: Optional[str] = None

class VoiceCommandType(str, Enum):
    HEALTH_LOGGING = "health_logging"
    APPOINTMENT = "appointment"
    EMERGENCY = "emergency"
    NAVIGATION = "navigation"
    INFORMATION = "information"

class VoiceCommandRequest(BaseModel):
    command_text: str
    command_type: VoiceCommandType 

class VoiceCommandResult(BaseModel):
    command_type: VoiceCommandType
    response_text: str
    success: bool
    action_taken: str 