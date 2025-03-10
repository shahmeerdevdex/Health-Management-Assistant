from pydantic import BaseModel

class PractitionerPatientLink(BaseModel):
    practitioner_id: int
    patient_id: int
