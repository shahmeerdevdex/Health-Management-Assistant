from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.crud.telehealth import create_telehealth_session, get_active_sessions
from app.schemas.telehealth import TelehealthSessionCreate, TelehealthSessionResponse
from typing import List
from app.api.endpoints.dependencies import get_current_user  # Import the correct authentication function
from app.db.models.telehealth import TelehealthSession  
from sqlalchemy.future import select

router = APIRouter()

@router.post("/start-session", response_model=TelehealthSessionResponse)
async def start_telehealth_session(
    session_data: TelehealthSessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)  # Fetches the authenticated user
):
    """
    Start a new telehealth session between a user and a practitioner.

    - Requires authentication via access token.
    - Creates a new telehealth session.
    - Returns the created telehealth session details.
    """
    return await create_telehealth_session(db, session_data)

@router.get("/sessions", response_model=List[TelehealthSessionResponse])
async def list_active_sessions(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)  # Fetches the authenticated user
):
    """
    Retrieve active telehealth sessions for the authenticated user.

    - Requires authentication via access token.
    - Returns a list of active telehealth sessions for the authenticated user.
    """
    return await get_active_sessions(db, current_user.id)  # Uses authenticated user's ID

@router.put("/end-session/{session_id}")
async def end_telehealth_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)  # Fetches the authenticated user
):
    """
    End a telehealth session by marking it as 'ended'.

    - Requires authentication via access token.
    - Only the user or the practitioner who initiated the session can end it.
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
