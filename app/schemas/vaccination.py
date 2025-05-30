from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import date, datetime


class VaccinationRecordRequest(BaseModel):
    user_id: int  # The user receiving the vaccination
    vaccine_name: str  # Name of the vaccine (e.g., "COVID-19 Pfizer", "Hepatitis B")
    dose_number: int  # Dose number (e.g., 1st, 2nd, booster)
    date_administered: date  # Date of vaccination
    healthcare_provider: str  # Clinic, hospital, or provider name
    next_due_date: Optional[date] = None  # Next scheduled dose (if applicable)
    user_email: Optional[EmailStr] = None  # Optional email for reminders
    user_phone: Optional[str] = None  # Optional phone number for SMS reminders


class VaccinationRecordResponse(BaseModel):
    record_id: int
    user_id: int
    vaccine_name: str
    dose_number: int
    date_administered: date
    healthcare_provider: str
    next_due_date: Optional[date]
    user_email: Optional[EmailStr] = None
    user_phone: Optional[str] = None


class VaccinationReminder(BaseModel):
    vaccine_name: str
    next_due_date: date
    reminder_sent_at: datetime
    healthcare_provider: Optional[str] = None


class VaccinationRemindersResponse(BaseModel):
    user_id: int
    reminders: List[VaccinationReminder]


class NationalImmunizationSyncResponse(BaseModel):
    user_id: int
    synced_records: List[VaccinationRecordResponse]
    message: str = "Vaccination records successfully synced with the national database."
