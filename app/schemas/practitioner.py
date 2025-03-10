from pydantic import BaseModel

class PractitionerCreate(BaseModel):
    name: str
    specialty: str
    contact_info: str

class PractitionerResponse(BaseModel):
    id: int
    name: str
    specialty: str
    contact_info: str

    class Config:
        from_attributes = True