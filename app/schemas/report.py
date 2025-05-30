from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from pydantic.functional_validators import BeforeValidator
from typing_extensions import Annotated

from dateutil.parser import parse as date_parse  # add this import

def ensure_timezone(dt: Optional[str]) -> Optional[datetime]:
    if dt is None:
        return None
    if isinstance(dt, str):
        dt = date_parse(dt)  # safely parse string to datetime
    if dt.tzinfo is None:
        return dt.replace(tzinfo=datetime.now().astimezone().tzinfo)
    return dt

TZAwareDateTime = Annotated[datetime, BeforeValidator(ensure_timezone)]


class ReportCreate(BaseModel):
    report_data: str

class CustomReportCreate(BaseModel):
    start_date: Optional[TZAwareDateTime] = None
    end_date: Optional[TZAwareDateTime] = None
    include_medications: bool = True
    include_appointments: bool = True
    include_vaccinations: bool = True
    include_chronic_data: bool = True

class ReportResponse(BaseModel):
    id: int
    user_id: int
    report_data: str
    generated_at: datetime

    class Config:
        from_attributes = True  
