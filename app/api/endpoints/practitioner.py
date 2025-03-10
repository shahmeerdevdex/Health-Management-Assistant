from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.practitioner import PractitionerCreate, PractitionerResponse
from app.crud.practitioner import create_practitioner, get_practitioners
from app.services.auth_service import verify_access_token
from typing import List

router = APIRouter()


@router.post("/practitioner/add", response_model=PractitionerResponse)
async def add_practitioner_endpoint(
    practitioner: PractitionerCreate,
    db: AsyncSession = Depends(get_db),
    token_data: dict = Depends(verify_access_token),
):
    """
    Add a new practitioner to the system.

    - **Requires Authentication** via access token.
    - **Parameters:**
        - `practitioner`: The details of the practitioner to add.
        - `db`: The database session.
        - `token_data`: The decoded access token to ensure authentication.
    - **Returns:** The newly created practitioner record.
    """
    return await create_practitioner(db, practitioner)


@router.get("/practitioner/list", response_model=List[PractitionerResponse])
async def list_practitioners(
    db: AsyncSession = Depends(get_db),
    token_data: dict = Depends(verify_access_token),
):
    """
    Retrieve the list of all practitioners.

    - **Requires Authentication** via access token.
    - **Parameters:**
        - `db`: The database session.
        - `token_data`: The decoded access token to ensure authentication.
    - **Returns:** A list of all practitioners stored in the database.
    """
    practitioners = await get_practitioners(db)
    return practitioners
