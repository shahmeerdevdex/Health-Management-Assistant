from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.monitoring import ChronicMonitoringRequest, ChronicMonitoringResponse
from app.services.monitoring_service import process_chronic_monitoring
from app.api.endpoints.dependencies import get_db,get_current_user
from sqlalchemy.future import select
from app.db.models.monitoring import ChronicMonitoring
from app.db.models.caregiver import CaregiverAssignment
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

@router.post("/chronic", response_model=ChronicMonitoringResponse)
async def chronic_disease_monitoring(
    request: ChronicMonitoringRequest,
    db: Session = Depends(get_db),
    db_user = Depends(get_current_user)
):
    """
    Processes and analyzes data for chronic disease monitoring, such as diabetes, hypertension, and cardiovascular health.
    """
    try:
        monitoring_data = await process_chronic_monitoring(request, db)
        return monitoring_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/monitoring/chronic/{patient_id}")
async def get_chronic_monitoring(patient_id: int, db: AsyncSession = Depends(get_db), db_user = Depends(get_current_user)):
    """
    Retrieve chronic disease monitoring records for a given patient.
    """
    result = await db.execute(select(ChronicMonitoring).where(ChronicMonitoring.patient_id == patient_id))
    records = result.scalars().all()
    if not records:
        raise HTTPException(status_code=404, detail="No chronic monitoring records found for this patient.")
    return records
