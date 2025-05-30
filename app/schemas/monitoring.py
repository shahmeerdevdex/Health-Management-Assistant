from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

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

class VitalSigns(BaseModel):
    heart_rate: Optional[float] = None
    blood_pressure: Optional[Dict[str, float]] = None
    blood_sugar: Optional[float] = None
    temperature: Optional[float] = None
    oxygen_saturation: Optional[float] = None

class PatientStatus(BaseModel):
    patient_id: int
    name: str
    latest_checkin: Optional[datetime] = None
    vital_signs: Optional[VitalSigns] = None
    risk_level: str = Field(..., pattern="^(low|moderate|high|unknown)$")
    active_alerts: List[str] = []

class CriticalAlert(BaseModel):
    patient_id: int
    patient_name: str
    alert_type: str
    details: List[Dict[str, Any]]
    timestamp: datetime

class AIInsight(BaseModel):
    patient_id: int
    patient_name: str
    insights: List[str]
    predictions: List[Dict[str, Any]]
    confidence_score: float = Field(..., ge=0, le=1)

class RiskAssessment(BaseModel):
    patient_id: int
    patient_name: str
    risk_factors: List[Dict[str, Any]]
    trends: List[Dict[str, Any]]
    recommendations: List[str]

class RealTimeMonitoringResponse(BaseModel):
    critical_alerts: List[CriticalAlert]
    patient_status: List[PatientStatus]
    ai_insights: List[AIInsight]
    risk_assessment: List[RiskAssessment]
