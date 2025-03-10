from pydantic import BaseModel
from datetime import datetime

class ReportCreate(BaseModel):
    report_data: str

class ReportResponse(BaseModel):
    id: int
    user_id: int
    report_data: str
    generated_at: datetime

    class Config:
        from_attributes = True  
