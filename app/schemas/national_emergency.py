from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class EmergencyAlertType(str, Enum):
    NATURAL_DISASTER = "natural_disaster"
    PUBLIC_HEALTH = "public_health"
    CIVIL_EMERGENCY = "civil_emergency"
    SECURITY_THREAT = "security_threat"
    INFRASTRUCTURE = "infrastructure"
    ENVIRONMENTAL = "environmental"
    OTHER = "other"

class EmergencySeverity(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"

class EmergencyRegion(BaseModel):
    name: str
    type: str  # city, state, region, etc.
    coordinates: Optional[Dict[str, float]] = None
    affected_areas: Optional[List[str]] = None
    population_impact: Optional[int] = None

class EmergencyResource(BaseModel):
    name: str
    type: str
    contact: str
    description: str
    location: Optional[str] = None
    capacity: Optional[int] = None
    status: str = "available"
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class EmergencyAlert(BaseModel):
    alert_id: str
    type: EmergencyAlertType
    severity: EmergencySeverity
    title: str
    description: str
    affected_regions: List[EmergencyRegion]
    start_time: datetime
    end_time: Optional[datetime] = None
    source: str
    official_guidance: List[str]
    resources: List[EmergencyResource]
    status: str = "active"
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    additional_info: Optional[Dict[str, Any]] = None

class EmergencyResponsePlan(BaseModel):
    plan_id: str
    alert_type: EmergencyAlertType
    severity_levels: Dict[EmergencySeverity, Dict[str, Any]]
    immediate_actions: List[str]
    resource_requirements: Dict[str, int]
    communication_protocols: List[str]
    evacuation_procedures: Optional[Dict[str, Any]] = None
    medical_response: Optional[Dict[str, Any]] = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class EmergencyAlertSubscription(BaseModel):
    user_id: int
    alert_types: List[EmergencyAlertType]
    regions: List[str]
    severity_threshold: EmergencySeverity
    notification_preferences: Dict[str, bool]
    active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class EmergencyAlertRequest(BaseModel):
    user_id: int
    location: Dict[str, float]  # latitude, longitude
    alert_types: Optional[List[EmergencyAlertType]] = None
    radius_km: Optional[float] = None
    include_resources: bool = True

class EmergencyAlertResponse(BaseModel):
    user_id: int
    active_alerts: List[EmergencyAlert]
    nearby_resources: List[EmergencyResource]
    recommended_actions: List[str]
    emergency_contacts: List[Dict[str, str]]
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    additional_guidance: Optional[Dict[str, Any]] = None 