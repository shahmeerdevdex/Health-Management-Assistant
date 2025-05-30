from pydantic import BaseModel
from typing import List, Optional

class MentalHealthMarketplaceRequest(BaseModel):
    user_id: int  # The user making the request
    location: Optional[str] = None  # User's location for filtering professionals
    specialties: Optional[List[str]] = None  # Types of mental health services needed
    insurance_coverage: Optional[bool] = False  # Whether insurance coverage is required
    online_consultation: Optional[bool] = False  # Whether online sessions are preferred

class MentalHealthProfessional(BaseModel):
    id: int
    name: str
    specialty: str
    location: str
    accepts_insurance: bool
    online_available: bool
    contact_info: str

class MentalHealthMarketplaceResponse(BaseModel):
    user_id: int
    available_professionals: List[MentalHealthProfessional]  # List of professionals matching the query
    message: str
