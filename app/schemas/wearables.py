from pydantic import BaseModel
from typing import List, Optional

class WearableDataRequest(BaseModel):
    device_id: str
    heart_rate: Optional[List[int]] = None  # Heart rate data over time
    sleep_patterns: Optional[List[dict]] = None  # Sleep stages and durations
    activity_levels: Optional[List[dict]] = None  # Steps, calories burned, etc.
    oxygen_saturation: Optional[List[float]] = None  # Blood oxygen levels
    temperature: Optional[List[float]] = None  # Body temperature readings

class WearableDataResponse(BaseModel):
    summary: str
    insights: Optional[List[str]] = None  # Key health insights based on the data
