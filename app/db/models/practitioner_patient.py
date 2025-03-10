from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base
from sqlalchemy import Table


practitioner_patient = Table(
    "practitioner_patient",
    Base.metadata,
    Column("practitioner_id", Integer, ForeignKey("practitioners.id")),
    Column("patient_id", Integer, ForeignKey("users.id")),
)
