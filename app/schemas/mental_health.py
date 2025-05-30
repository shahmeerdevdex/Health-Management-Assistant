from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class TherapyType(str, Enum):
    INDIVIDUAL = "individual"
    GROUP = "group"
    COUPLES = "couples"
    FAMILY = "family"
    CRISIS = "crisis"

class TherapyApproach(str, Enum):
    CBT = "cognitive_behavioral"
    DBT = "dialectical_behavioral"
    PSYCHODYNAMIC = "psychodynamic"
    HUMANISTIC = "humanistic"
    MINDFULNESS = "mindfulness"
    OTHER = "other"

class ProfessionalBase(BaseModel):
    name: str
    email: str
    specialty: str
    location: str
    accepts_insurance: bool = False
    online_available: bool = True
    contact_info: Optional[str] = None
    credentials: Optional[List[str]] = None
    languages: Optional[List[str]] = None
    specialties: Optional[List[str]] = None
    availability: Optional[Dict[str, Any]] = None
    emergency_available: bool = False
    therapy_types: Optional[List[TherapyType]] = None
    approaches: Optional[List[TherapyApproach]] = None
    session_duration: int = 50
    session_fee: Optional[float] = None
    sliding_scale: bool = False
    min_fee: Optional[float] = None
    max_fee: Optional[float] = None

class ProfessionalCreate(ProfessionalBase):
    user_id: Optional[int] = None

class ProfessionalUpdate(BaseModel):
    name: Optional[str] = None
    specialty: Optional[str] = None
    location: Optional[str] = None
    accepts_insurance: Optional[bool] = None
    online_available: Optional[bool] = None
    contact_info: Optional[str] = None
    credentials: Optional[List[str]] = None
    languages: Optional[List[str]] = None
    specialties: Optional[List[str]] = None
    availability: Optional[Dict[str, Any]] = None
    emergency_available: Optional[bool] = None
    therapy_types: Optional[List[TherapyType]] = None
    approaches: Optional[List[TherapyApproach]] = None
    session_duration: Optional[int] = None
    session_fee: Optional[float] = None
    sliding_scale: Optional[bool] = None
    min_fee: Optional[float] = None
    max_fee: Optional[float] = None

class ProfessionalResponse(ProfessionalBase):
    id: int
    user_id: int
    rating: float

    class Config:
        from_attributes = True

class TherapistAppointmentBase(BaseModel):
    user_id: int
    therapist_id: int
    date_time: datetime
    session_type: TherapyType
    approach: Optional[TherapyApproach] = None
    notes: Optional[str] = None
    follow_up_required: bool = False
    follow_up_date: Optional[datetime] = None
    session_summary: Optional[str] = None
    goals_discussed: Optional[List[str]] = None
    homework_assigned: Optional[List[str]] = None
    next_session_agenda: Optional[str] = None

class TherapistAppointmentCreate(TherapistAppointmentBase):
    pass

class TherapistAppointmentUpdate(BaseModel):
    status: Optional[str] = Field(None, pattern="^(Pending|Confirmed|Completed|Cancelled)$")
    payment_status: Optional[str] = Field(None, pattern="^(Pending|Paid|Refunded)$")
    video_call_link: Optional[str] = None
    notes: Optional[str] = None
    follow_up_required: Optional[bool] = None
    follow_up_date: Optional[datetime] = None
    session_summary: Optional[str] = None
    goals_discussed: Optional[List[str]] = None
    homework_assigned: Optional[List[str]] = None
    next_session_agenda: Optional[str] = None

class TherapistAppointmentResponse(TherapistAppointmentBase):
    id: int
    status: str
    payment_status: str
    video_call_link: Optional[str]

    class Config:
        from_attributes = True

class MentalHealthAssessmentBase(BaseModel):
    user_id: int
    assessment_type: str = Field(..., pattern="^(PHQ-9|GAD-7|PSS-10|BDI|Other)$")
    scores: Dict[str, int]
    total_score: int
    risk_level: str = Field(..., pattern="^(Low|Moderate|High)$")
    recommendations: Optional[List[str]] = None
    follow_up_date: Optional[datetime] = None
    notes: Optional[str] = None
    therapist_id: Optional[int] = None
    assessment_tools: Optional[List[str]] = None
    symptoms: Optional[List[str]] = None
    triggers: Optional[List[str]] = None
    coping_strategies: Optional[List[str]] = None
    support_system: Optional[List[str]] = None

class MentalHealthAssessmentCreate(MentalHealthAssessmentBase):
    pass

class MentalHealthAssessmentUpdate(BaseModel):
    scores: Optional[Dict[str, int]] = None
    total_score: Optional[int] = None
    risk_level: Optional[str] = Field(None, pattern="^(Low|Moderate|High)$")
    recommendations: Optional[List[str]] = None
    follow_up_date: Optional[datetime] = None
    notes: Optional[str] = None
    symptoms: Optional[List[str]] = None
    triggers: Optional[List[str]] = None
    coping_strategies: Optional[List[str]] = None
    support_system: Optional[List[str]] = None

class MentalHealthAssessmentResponse(MentalHealthAssessmentBase):
    id: int
    date: datetime
    therapist_id: Optional[int]

    class Config:
        from_attributes = True

class TherapistReviewBase(BaseModel):
    user_id: int
    therapist_id: int
    rating: float = Field(..., ge=1, le=5)
    review_text: Optional[str] = None
    therapy_type: Optional[TherapyType] = None
    approach: Optional[TherapyApproach] = None
    session_date: Optional[datetime] = None

class TherapistReviewCreate(TherapistReviewBase):
    pass

class TherapistReviewUpdate(BaseModel):
    rating: Optional[float] = Field(None, ge=1, le=5)
    review_text: Optional[str] = None
    helpful_votes: Optional[int] = None

class TherapistReviewResponse(TherapistReviewBase):
    id: int
    date: datetime
    helpful_votes: int
    verified_session: bool

    class Config:
        from_attributes = True

class MentalHealthResourceBase(BaseModel):
    title: str
    content_type: str
    content: str
    tags: Optional[List[str]] = None
    difficulty_level: str = Field(..., pattern="^(beginner|intermediate|advanced)$")
    author: Optional[str] = None
    source: Optional[str] = None
    is_verified: bool = False
    target_audience: Optional[List[str]] = None
    related_conditions: Optional[List[str]] = None
    estimated_time: Optional[int] = None
    prerequisites: Optional[List[str]] = None
    learning_objectives: Optional[List[str]] = None

class MentalHealthResourceCreate(MentalHealthResourceBase):
    pass

class MentalHealthResourceUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None
    difficulty_level: Optional[str] = Field(None, pattern="^(beginner|intermediate|advanced)$")
    is_verified: Optional[bool] = None
    target_audience: Optional[List[str]] = None
    related_conditions: Optional[List[str]] = None
    estimated_time: Optional[int] = None
    prerequisites: Optional[List[str]] = None
    learning_objectives: Optional[List[str]] = None

class MentalHealthResourceResponse(MentalHealthResourceBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CrisisInterventionBase(BaseModel):
    user_id: int
    crisis_type: str
    severity: str = Field(..., pattern="^(Low|Moderate|High|Emergency)$")
    intervention_type: str
    responder_id: Optional[int] = None
    actions_taken: List[str]
    outcome: str
    follow_up_required: bool = True
    follow_up_date: Optional[datetime] = None
    notes: Optional[str] = None
    emergency_services_contacted: bool = False
    safety_plan_created: bool = False
    support_network_contacted: Optional[List[str]] = None

class CrisisInterventionCreate(CrisisInterventionBase):
    pass

class CrisisInterventionUpdate(BaseModel):
    severity: Optional[str] = Field(None, pattern="^(Low|Moderate|High|Emergency)$")
    actions_taken: Optional[List[str]] = None
    outcome: Optional[str] = None
    follow_up_required: Optional[bool] = None
    follow_up_date: Optional[datetime] = None
    notes: Optional[str] = None
    emergency_services_contacted: Optional[bool] = None
    safety_plan_created: Optional[bool] = None
    support_network_contacted: Optional[List[str]] = None

class CrisisInterventionResponse(CrisisInterventionBase):
    id: int
    date_time: datetime
    responder_id: Optional[int]

    class Config:
        from_attributes = True

class MentalHealthHistoryResponse(BaseModel):
    assessments: List[MentalHealthAssessmentResponse]
    crisis_interventions: List[CrisisInterventionResponse]
    appointments: List[TherapistAppointmentResponse]
    resources_accessed: List[MentalHealthResourceResponse]
    summary: Dict[str, Any]

    class Config:
        from_attributes = True 