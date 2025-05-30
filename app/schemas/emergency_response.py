from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from app.db.models.emergency_response import (
    EmergencyType,
    EmergencySeverity,
    EmergencyStatus
)

class EmergencyResponseBase(BaseModel):
    emergency_type: EmergencyType
    severity: EmergencySeverity
    location_lat: float
    location_lon: float
    description: str

class EmergencyResponseCreate(EmergencyResponseBase):
    user_id: int
    geocoded_address: Optional[str] = None

class EmergencyResponseUpdate(BaseModel):
    status: Optional[EmergencyStatus] = None
    description: Optional[str] = None
    location_lat: Optional[float] = None
    location_lon: Optional[float] = None
    severity: Optional[EmergencySeverity] = None
    geocoded_address: Optional[str] = None
    traffic_conditions: Optional[Dict[str, Any]] = None

class EmergencyResponseInDB(EmergencyResponseBase):
    id: int
    user_id: int
    status: EmergencyStatus
    created_at: datetime
    dispatched_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    updated_at: datetime
    estimated_response_time: Optional[int] = None
    route_information: Optional[Dict[str, Any]] = None
    geocoded_address: Optional[str] = None
    traffic_conditions: Optional[Dict[str, Any]] = None
    distance_matrix: Optional[Dict[str, Any]] = None
    optimized_route: Optional[Dict[str, Any]] = None

    class Config:
        orm_mode = True

class EmergencyResourceBase(BaseModel):
    type: str
    name: str
    contact: str  # Required contact information
    location_lat: float
    location_lon: float
    capability_score: float = 1.0

class EmergencyResourceCreate(EmergencyResourceBase):
    pass

class EmergencyResourceUpdate(BaseModel):
    availability: Optional[bool] = None
    location_lat: Optional[float] = None
    location_lon: Optional[float] = None
    capability_score: Optional[float] = None

class EmergencyResourceInDB(EmergencyResourceBase):
    id: int
    availability: bool
    assigned_user_id: Optional[int] = None
    current_emergency_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class EmergencyTeamBase(BaseModel):
    name: str
    type: str
    leader_id: int

class EmergencyTeamCreate(EmergencyTeamBase):
    member_ids: List[int] = []

class EmergencyTeamUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    leader_id: Optional[int] = None
    status: Optional[str] = None

class EmergencyTeamInDB(EmergencyTeamBase):
    id: int
    status: str
    created_at: datetime
    updated_at: datetime
    member_ids: List[int] = []

    class Config:
        orm_mode = True

class EmergencyZoneBase(BaseModel):
    name: str
    center_lat: float
    center_lon: float
    radius_km: float
    type: str
    protocol: Optional[Dict[str, Any]] = None

class EmergencyZoneCreate(EmergencyZoneBase):
    pass

class EmergencyZoneUpdate(BaseModel):
    name: Optional[str] = None
    center_lat: Optional[float] = None
    center_lon: Optional[float] = None
    radius_km: Optional[float] = None
    type: Optional[str] = None
    protocol: Optional[Dict[str, Any]] = None

class EmergencyZoneInDB(EmergencyZoneBase):
    id: int
    active_emergencies: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class EmergencyDispatchBase(BaseModel):
    emergency_id: int
    resource_id: int
    status: str
    notes: Optional[str] = None

class EmergencyDispatchCreate(EmergencyDispatchBase):
    pass

class EmergencyDispatchUpdate(BaseModel):
    status: Optional[str] = None
    arrival_time: Optional[datetime] = None
    completion_time: Optional[datetime] = None
    notes: Optional[str] = None

class EmergencyDispatchInDB(EmergencyDispatchBase):
    id: int
    dispatch_time: datetime
    arrival_time: Optional[datetime] = None
    completion_time: Optional[datetime] = None

    class Config:
        orm_mode = True

class EmergencyTrackingBase(BaseModel):
    emergency_id: int
    status: str
    location_lat: float
    location_lon: float
    meta_data: Optional[Dict[str, Any]] = None

class EmergencyTrackingCreate(EmergencyTrackingBase):
    pass

class EmergencyTrackingUpdate(BaseModel):
    status: Optional[str] = None
    location_lat: Optional[float] = None
    location_lon: Optional[float] = None
    meta_data: Optional[Dict[str, Any]] = None

class EmergencyTrackingInDB(EmergencyTrackingBase):
    id: int
    last_updated: datetime

    class Config:
        orm_mode = True

class EmergencyResourceInventoryBase(BaseModel):
    resource_id: int
    item_type: str
    quantity: int
    minimum_quantity: int
    maximum_quantity: int
    notes: Optional[str] = None

class EmergencyResourceInventoryCreate(EmergencyResourceInventoryBase):
    pass

class EmergencyResourceInventoryUpdate(BaseModel):
    quantity: Optional[int] = None
    minimum_quantity: Optional[int] = None
    maximum_quantity: Optional[int] = None
    notes: Optional[str] = None

class EmergencyResourceInventoryInDB(EmergencyResourceInventoryBase):
    id: int
    last_restocked: datetime

    class Config:
        orm_mode = True

class EmergencyAnalytics(BaseModel):
    total_emergencies: int
    average_response_time: float
    average_resolution_time: float
    resource_utilization: Dict[str, int]
    emergency_types: Dict[str, int]
    zone_activity: Dict[int, int]

class EmergencyProtocolBase(BaseModel):
    name: str  # Required name for the protocol
    emergency_type: EmergencyType
    severity: EmergencySeverity
    steps: List[str]
    success_criteria: List[str]
    is_active: bool = True
    last_reviewed: datetime = Field(default_factory=lambda: datetime.now())  # Using timezone-naive datetime

class EmergencyProtocolCreate(EmergencyProtocolBase):
    pass

class EmergencyProtocolUpdate(BaseModel):
    steps: Optional[List[str]] = None
    success_criteria: Optional[List[str]] = None
    is_active: Optional[bool] = None

class EmergencyProtocolInDB(EmergencyProtocolBase):
    id: int
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now())
    updated_at: Optional[datetime] = Field(default_factory=lambda: datetime.now())

    class Config:
        orm_mode = True

# EmergencyResponseResponse schema
class EmergencyResponseResponse(EmergencyResponseInDB):
    pass

# EmergencyResourceResponse schema
class EmergencyResourceResponse(EmergencyResourceInDB):
    pass

# EmergencyProtocolResponse schema
class EmergencyProtocolResponse(EmergencyProtocolBase):
    id: int

    class Config:
        from_attributes = True

class EmergencyTrainingBase(BaseModel):
    user_id: int
    training_type: str
    certification_id: Optional[str] = None
    issue_date: datetime
    expiry_date: Optional[datetime] = None
    provider: str
    status: str
    verification_document: Optional[str] = None
    notes: Optional[str] = None

    def dict(self, *args, **kwargs):
        d = super().dict(*args, **kwargs)
        # Convert timezone-aware datetimes to naive datetimes
        if d.get('issue_date') and d['issue_date'].tzinfo is not None:
            d['issue_date'] = d['issue_date'].replace(tzinfo=None)
        if d.get('expiry_date') and d['expiry_date'].tzinfo is not None:
            d['expiry_date'] = d['expiry_date'].replace(tzinfo=None)
        return d

class EmergencyTrainingCreate(EmergencyTrainingBase):
    pass

class EmergencyTrainingUpdate(BaseModel):
    training_type: Optional[str] = None
    certification_id: Optional[str] = None
    issue_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    provider: Optional[str] = None
    status: Optional[str] = None
    verification_document: Optional[str] = None
    notes: Optional[str] = None

class EmergencyTrainingResponse(EmergencyTrainingBase):
    id: int

    class Config:
        from_attributes = True

# EmergencyTeamResponse schema
class EmergencyTeamResponse(EmergencyTeamInDB):
    pass

# EmergencyZoneResponse schema
class EmergencyZoneResponse(EmergencyZoneInDB):
    pass

# EmergencyDispatchResponse schema
class EmergencyDispatchResponse(EmergencyDispatchInDB):
    pass

# EmergencyTrackingResponse schema
class EmergencyTrackingResponse(EmergencyTrackingInDB):
    pass

# EmergencyResourceInventoryResponse schema
class EmergencyResourceInventoryResponse(EmergencyResourceInventoryInDB):
    pass

# Add new schema for Google Maps related data
class GoogleMapsRouteInfo(BaseModel):
    distance: Dict[str, Any]  # Distance information
    duration: Dict[str, Any]  # Duration information
    steps: List[Dict[str, Any]]  # Turn-by-turn directions
    polyline: str  # Encoded polyline for the route
    traffic_conditions: Optional[Dict[str, Any]] = None

class GoogleMapsDistanceMatrix(BaseModel):
    origins: List[Dict[str, float]]  # List of origin coordinates
    destinations: List[Dict[str, float]]  # List of destination coordinates
    distances: List[Dict[str, Any]]  # Distance information for each origin-destination pair
    durations: List[Dict[str, Any]]  # Duration information for each origin-destination pair
        