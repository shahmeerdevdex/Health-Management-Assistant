from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.future import select
from datetime import datetime

from app.schemas.caregiver import CaregiverRequest, CaregiverResponse
from app.db.models.caregiver import CaregiverAssignment
from app.db.models.user import User

async def process_caregiver_management(request: CaregiverRequest, db: AsyncSession) -> CaregiverResponse:
    """
    Stores caregiver assignments in the database and returns confirmation.
    """

    # Optional: internal FK validation
    caregiver = (await db.execute(select(User).where(User.id == request.user_id))).scalar_one_or_none()
    if not caregiver:
        raise Exception(f"Caregiver ID {request.user_id} not found")
    
    patient = (await db.execute(select(User).where(User.id == request.patient_id))).scalar_one_or_none()
    if not patient:
        raise Exception(f"Patient ID {request.patient_id} not found")

    if request.user_id == request.patient_id:
        raise Exception("A user cannot be assigned as their own caregiver")

    try:
        caregiver_assignment = CaregiverAssignment(
            caregiver_id=request.user_id,
            patient_id=request.patient_id,
            tasks=request.tasks,
            schedule=request.schedule,
            emergency_contact=request.emergency_contact,
            appointment_history=request.appointment_history,
            medication_tracking=request.medication_tracking,
            monitoring_data=request.monitoring_data,
            financial_support=request.financial_support,
            assigned_at=datetime.utcnow()
        )
        db.add(caregiver_assignment)
        await db.commit()
        await db.refresh(caregiver_assignment)
    except SQLAlchemyError as e:
        await db.rollback()
        raise Exception(f"Database error: {str(e)}")
    
    return CaregiverResponse(
        user_id=request.user_id,
        patient_id=request.patient_id,
        assigned_tasks=request.tasks,
        appointment_history=request.appointment_history,
        medication_tracking=request.medication_tracking,
        monitoring_data=request.monitoring_data,
        financial_support=request.financial_support,
        message=f"Caregiver {request.user_id} assigned to patient {request.patient_id} with {len(request.tasks)} tasks."
    )
