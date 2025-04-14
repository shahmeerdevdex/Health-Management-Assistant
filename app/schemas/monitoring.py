from pydantic import BaseModel, Field
from typing import List, Optional

class BloodPressureReading(BaseModel):
    systolic: int
    diastolic: int

class ChronicMonitoringRequest(BaseModel):
    patient_id: int  # Changed from str to int to match DB model
    condition: str = Field(..., description="e.g., 'diabetes', 'hypertension'")
    blood_pressure: Optional[List[BloodPressureReading]] = Field(default_factory=list)
    blood_sugar: Optional[List[float]] = Field(default_factory=list)
    heart_rate: Optional[List[int]] = Field(default_factory=list)
    weight: Optional[List[float]] = Field(default_factory=list)
    medications: Optional[List[str]] = Field(default_factory=list)

class ChronicMonitoringResponse(BaseModel):
    summary: str
    insights: Optional[List[str]] = None
