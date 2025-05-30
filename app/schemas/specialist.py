from enum import Enum
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class SpecialistType(str, Enum):
    CARDIOLOGIST = "cardiologist"
    NEUROLOGIST = "neurologist"
    DERMATOLOGIST = "dermatologist"
    ORTHOPEDIST = "orthopedist"
    PEDIATRICIAN = "pediatrician"
    PSYCHIATRIST = "psychiatrist"
    GYNECOLOGIST = "gynecologist"
    OPHTHALMOLOGIST = "ophthalmologist"
    ENT = "ent"
    GASTROENTEROLOGIST = "gastroenterologist"
    ENDOCRINOLOGIST = "endocrinologist"
    RHEUMATOLOGIST = "rheumatologist"
    UROLOGIST = "urologist"
    ONCOLOGIST = "oncologist"
    PULMONOLOGIST = "pulmonologist"
    NEPHROLOGIST = "nephrologist"
    HEMATOLOGIST = "hematologist"
    INFECTIOUS_DISEASE = "infectious_disease"
    ALLERGIST = "allergist"
    IMMUNOLOGIST = "immunologist"
    GERIATRICIAN = "geriatrician"
    SPORTS_MEDICINE = "sports_medicine"
    REHABILITATION = "rehabilitation"
    PAIN_MANAGEMENT = "pain_management"
    SLEEP_MEDICINE = "sleep_medicine"
    PALLIATIVE_CARE = "palliative_care"
    OTHER = "other"

class SpecialistBase(BaseModel):
    specialist_type: SpecialistType
    qualifications: List[str]
    years_of_experience: int
    areas_of_expertise: List[str]
    languages_spoken: List[str]
    accepting_new_patients: bool = True
    telehealth_available: bool = False
    hospital_affiliations: Optional[List[str]] = None
    research_interests: Optional[List[str]] = None
    publications: Optional[List[str]] = None

class SpecialistCreate(SpecialistBase):
    pass

class SpecialistResponse(SpecialistBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 