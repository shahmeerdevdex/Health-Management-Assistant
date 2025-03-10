from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase): 
    pass


from app.db.models.user import User
from app.db.models.appointments import Appointment
from app.db.models.health_diary import HealthDiary
from app.db.models.health_tips import HealthTip
from app.db.models.medication import Medication
from app.db.models.medication_logs import MedicationLog
from app.db.models.notifications import Notification
from app.db.models.practitioner_patient import practitioner_patient
from app.db.models.reports import Report
from app.db.models.roles import Role
from app.db.models.symptom_analysis import SymptomAnalysis
from app.db.models.practitioners import Practitioner
from app.db.models.telehealth import TelehealthSession
