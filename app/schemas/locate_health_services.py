from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class HealthServiceRequest(BaseModel):
    latitude: float
    longitude: float
    radius: Optional[int] = 5000  # Default search radius in meters

class RealTimeData(BaseModel):
    is_available: bool
    estimated_wait_time: int  # minutes
    current_capacity: str
    last_updated: datetime

class SpecializedService(BaseModel):
    name: str
    level: Optional[str] = None
    certification: Optional[str] = None
    available: bool

class EmergencyServices(BaseModel):
    emergency_department: bool
    trauma_center: bool
    stroke_center: bool
    cardiac_care: bool
    pediatric_emergency: bool
    twenty_four_hour_service: bool

class AccessibilityInfo(BaseModel):
    wheelchair_accessible: bool
    accessible_parking: bool
    accessible_entrance: bool
    accessible_restrooms: bool
    sign_language_available: bool
    braille_available: bool

class HealthServiceResponse(BaseModel):
    name: str
    address: str
    latitude: float
    longitude: float
    rating: Optional[float] = None
    category: str
    phone: Optional[str] = None
    website: Optional[str] = None
    opening_hours: Optional[List[str]] = None
    types: Optional[List[str]] = None
    real_time_data: RealTimeData
    specialized_services: List[SpecializedService]
    emergency_services: EmergencyServices
    accessibility_info: AccessibilityInfo

    class Config:
        from_attributes = True

class RouteResponse(BaseModel):
    distance: str
    duration: str
    steps: List[Dict[str, Any]]
    polyline: str

class FacilityAvailabilityResponse(BaseModel):
    date: datetime
    available_slots: List[Dict[str, str]]
    capacity: Dict[str, int]