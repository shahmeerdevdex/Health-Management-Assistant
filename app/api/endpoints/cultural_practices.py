from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional, List
from datetime import datetime
from app.services.cultural_practice_service import CulturalPracticeService
from app.schemas.indigenous_health import IndigenousCommunity
from app.api.endpoints.dependencies import get_db, get_current_user
from app.schemas.user import User

router = APIRouter()

@router.post("/healing-session")
async def schedule_healing_session(
    community: IndigenousCommunity = Body(...),
    session_type: str = Body(...),
    participant_id: int = Body(...),
    healer_id: int = Body(...),
    scheduled_time: datetime = Body(...),
    notes: Optional[str] = Body(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Schedule a traditional healing session.
    """
    try:
        service = CulturalPracticeService(db)
        session = await service.schedule_healing_session(
            community,
            session_type,
            participant_id,
            healer_id,
            scheduled_time,
            notes
        )
        return session
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ceremony")
async def coordinate_ceremony(
    community: IndigenousCommunity = Body(...),
    ceremony_type: str = Body(...),
    date: datetime = Body(...),
    location: str = Body(...),
    participants: List[int] = Body(...),
    requirements: List[str] = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Coordinate a cultural ceremony.
    """
    try:
        service = CulturalPracticeService(db)
        ceremony = await service.coordinate_ceremony(
            community,
            ceremony_type,
            date,
            location,
            participants,
            requirements
        )
        return ceremony
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/traditional-medicine")
async def track_traditional_medicine(
    community: IndigenousCommunity = Body(...),
    medicine_id: int = Body(...),
    patient_id: int = Body(...),
    dosage: str = Body(...),
    frequency: str = Body(...),
    start_date: datetime = Body(...),
    end_date: Optional[datetime] = Body(None),
    notes: Optional[str] = Body(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Track traditional medicine administration.
    """
    try:
        service = CulturalPracticeService(db)
        tracking = await service.track_traditional_medicine(
            community,
            medicine_id,
            patient_id,
            dosage,
            frequency,
            start_date,
            end_date,
            notes
        )
        return tracking
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/support-group")
async def manage_support_group(
    community: IndigenousCommunity = Body(...),
    group_type: str = Body(...),
    participants: List[int] = Body(...),
    meeting_schedule: List[datetime] = Body(...),
    location: str = Body(...),
    facilitator_id: int = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Manage a cultural support group.
    """
    try:
        service = CulturalPracticeService(db)
        group = await service.manage_support_group(
            community,
            group_type,
            participants,
            meeting_schedule,
            location,
            facilitator_id
        )
        return group
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/schedule/{community}")
async def get_cultural_practice_schedule(
    community: IndigenousCommunity,
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get schedule of cultural practices and ceremonies.
    """
    try:
        service = CulturalPracticeService(db)
        schedule = await service.get_cultural_practice_schedule(
            community,
            start_date,
            end_date
        )
        return schedule
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 