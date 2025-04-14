from pydantic import BaseModel
from typing import Optional

class HealthServiceRequest(BaseModel):
    latitude: float
    longitude: float
    radius: Optional[int] = 5000  # Default search radius in meters

class HealthServiceResponse(BaseModel):
    name: str
    address: str
    latitude: float  # Added latitude field
    longitude: float  # Added longitude field
    rating: Optional[float] = None
    category: str  # Renamed 'type' to 'category' for consistency
    location: dict