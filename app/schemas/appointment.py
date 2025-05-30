from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from app.db.models.appointments import AppointmentStatus, AppointmentType, ProviderType

class AppointmentBase(BaseModel):
    provider_type: ProviderType
    provider_id: int
    date: datetime
    duration: int = Field(default=30, ge=15, le=180)  # Duration in minutes
    location: Optional[str] = None
    appointment_type: AppointmentType = AppointmentType.REGULAR
    notes: Optional[str] = None
    follow_up_required: bool = False
    follow_up_date: Optional[datetime] = None
    session_summary: Optional[str] = None
    goals_discussed: Optional[List[str]] = None
    homework_assigned: Optional[List[str]] = None
    next_session_agenda: Optional[str] = None
    video_call_link: Optional[str] = None

class AppointmentCreate(AppointmentBase):
    pass

class AppointmentUpdate(BaseModel):
    date: Optional[datetime] = None
    duration: Optional[int] = Field(None, ge=15, le=180)
    location: Optional[str] = None
    appointment_type: Optional[AppointmentType] = None
    status: Optional[AppointmentStatus] = None
    notes: Optional[str] = None
    follow_up_required: Optional[bool] = None
    follow_up_date: Optional[datetime] = None
    session_summary: Optional[str] = None
    goals_discussed: Optional[List[str]] = None
    homework_assigned: Optional[List[str]] = None
    next_session_agenda: Optional[str] = None
    video_call_link: Optional[str] = None

class AppointmentResponse(AppointmentBase):
    id: int
    user_id: int
    status: AppointmentStatus
    reminder_sent: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class AppointmentFilter(BaseModel):
    start_date: Optional[datetime] = Field(
        None,
        description="Start date for filtering appointments",
        example="2025-05-25T21:53:25.633Z"
    )
    end_date: Optional[datetime] = Field(
        None,
        description="End date for filtering appointments",
        example="2025-05-26T21:53:25.633Z"
    )
    status: Optional[AppointmentStatus] = Field(
        None,
        description="Appointment status filter",
        example="scheduled"
    )
    appointment_type: Optional[AppointmentType] = Field(
        None,
        description="Type of appointment",
        example="regular"
    )
    provider_type: Optional[ProviderType] = Field(
        None,
        description="Type of provider (practitioner/professional)",
        example="practitioner"
    )
    provider_id: Optional[int] = Field(
        None,
        description="ID of the provider",
        example=2
    )

    class Config:
        json_schema_extra = {
            "example": {
                "start_date": "2025-05-25T21:53:25.633Z",
                "end_date": "2025-05-26T21:53:25.633Z",
                "status": "scheduled",
                "appointment_type": "regular",
                "provider_type": "practitioner",
                "provider_id": 2
            }
        }

class ProviderAppointmentSummary(BaseModel):
    provider_id: int
    provider_type: ProviderType
    provider_name: str
    total_appointments: int
    upcoming_appointments: int
    completed_appointments: int
    cancelled_appointments: int
    average_rating: Optional[float] = None
