from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Dict, List
from datetime import datetime


class HealthMetrics(BaseModel):
    """Detailed health metrics submitted by a user during check-in."""

    heart_rate: Optional[int] = Field(None, description="Heart rate in beats per minute")
    blood_pressure: Optional[Dict[str, int]] = Field(
        None, example={"systolic": 120, "diastolic": 80}, description="Blood pressure readings"
    )
    blood_sugar: Optional[float] = Field(None, description="Blood sugar level (mg/dL)")
    temperature: Optional[float] = Field(None, description="Body temperature in Celsius or Fahrenheit")
    symptoms: Optional[List[str]] = Field(None, description="List of reported symptoms")
    mood: Optional[int] = Field(None, ge=1, le=5, description="Mood rating from 1 (low) to 5 (high)")
    sleep_hours: Optional[float] = Field(None, description="Number of hours slept")
    stress_level: Optional[int] = Field(None, ge=1, le=5, description="Stress level rating from 1 to 5")
    medication_taken: Optional[bool] = Field(None, description="Whether medication was taken")
    notes: Optional[str] = Field(None, description="Freeform notes or observations")


class HealthCheckInCreate(BaseModel):
    """Request model for creating a health check-in."""

    user_id: int
    health_metrics: HealthMetrics
    check_in_time: Optional[datetime] = Field(
        default_factory=datetime.utcnow, description="Timestamp of the check-in"
    )


class HealthCheckInResponse(BaseModel):
    """Response model for a recorded health check-in."""

    id: int
    user_id: int
    check_in_time: datetime
    health_metrics: HealthMetrics
    risk_score: Optional[float] = Field(None, description="AI-evaluated health risk score")
    requires_attention: bool = Field(..., description="Whether medical attention is needed")
    attention_reason: Optional[str] = Field(None, description="Reason for flagging this check-in")
    notification_sent: bool = Field(..., description="Whether a notification was sent")
    notification_time: Optional[datetime] = Field(None, description="Time notification was sent")

    class Config:
        from_attributes = True


from typing import Optional
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime

class ReminderPreferences(BaseModel):
    email: Optional[bool] = Field(default=True, description="Receive email notifications")
    push: Optional[bool] = Field(default=True, description="Receive push notifications")
    sms: Optional[bool] = Field(default=False, description="Receive SMS notifications")

class CheckInScheduleCreate(BaseModel):
    """User preferences for automatic health check-in reminders."""

    user_id: int
    frequency: str = Field(
        ..., 
        pattern="^(daily|weekly|biweekly|monthly)$", 
        description="Check-in frequency (daily, weekly, etc.)"
    )
    preferred_time: Optional[str] = Field(
        None,
        pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$",
        description="Preferred check-in time in HH:MM (24-hour format)"
    )
    reminder_preferences: Optional[ReminderPreferences] = Field(
        default_factory=ReminderPreferences,
        description="Notification channels for check-in reminders"
    )

class CheckInScheduleResponse(CheckInScheduleCreate):
    id: int
    is_active: bool
    last_check_in: Optional[datetime]
    next_check_in: Optional[datetime]

    class Config:
        from_attributes = True
