from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.crud.telehealth import create_telehealth_session, get_active_sessions
from app.schemas.telehealth import TelehealthSessionCreate, TelehealthSessionResponse
from typing import List
from app.services.auth_service import verify_access_token
from app.db.models.user import User  
from app.db.models.telehealth import TelehealthSession  
from sqlalchemy.future import select
from app.api.endpoints.dependencies import get_current_user


router = APIRouter()

@router.post("/telehealth/start-session", response_model=TelehealthSessionResponse)
async def start_telehealth_session(
    session_data: TelehealthSessionCreate,
    db: AsyncSession = Depends(get_db),
    token_data: dict = Depends(verify_access_token),
):
    """
    Start a new telehealth session between a user and a practitioner.
    Requires authentication.
    """
    return await create_telehealth_session(db, session_data)

@router.get("/telehealth/sessions", response_model=List[TelehealthSessionResponse])
async def list_active_sessions(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    token_data: dict = Depends(verify_access_token),
):
    """
    Retrieve active telehealth sessions for a user.
    """
    return await get_active_sessions(db, user_id)


@router.put("/telehealth/end-session/{session_id}")
async def end_telehealth_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    End a telehealth session by marking it as 'ended'.
    Only the user or the practitioner who initiated the session can end it.
    """
    result = await db.execute(select(TelehealthSession).where(TelehealthSession.id == session_id))
    session = result.scalars().first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Ensure that the current user is either the user or the practitioner in the session
    if session.user_id != current_user.id and session.practitioner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to end this session")

    session.session_status = "ended"
    await db.commit()

    return {"message": f"Telehealth session {session_id} has been ended successfully"}