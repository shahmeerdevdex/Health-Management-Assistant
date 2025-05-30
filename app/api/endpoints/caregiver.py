from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Dict, Any
from datetime import datetime
from app.core.security import hash_password

from app.schemas.caregiver import (
    CaregiverRequest, CaregiverResponse, 
    CaregiverAssignmentResponse, CaregiverProfileResponse
)
from app.schemas.user import UserCreate
from app.services.caregiver_service import process_caregiver_management
from app.api.endpoints.dependencies import get_db, get_current_user
from app.db.models.caregiver import CaregiverAssignment, Caregiver
from app.db.models.user import User, UserRoleInput
from app.db.models.practitioners import Practitioner
from app.db.models.mental_health import Professional

router = APIRouter()

@router.post("/create", response_model=CaregiverProfileResponse)
async def create_caregiver(
    email: str,
    password: str,
    full_name: str,
    phone: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new user with CAREGIVER role and their caregiver profile.
    """
    # Check if user with email already exists
    existing_user = await db.execute(
        select(User).where(User.email == email)
    )
    if existing_user.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="User with this email already exists"
        )

    try:
        # Create new user with CAREGIVER role
        new_user = User(
            email=email,
            password_hash=hash_password(password),
            full_name=full_name,
            role=UserRoleInput.CAREGIVER,
            is_active=True,
            created_at=datetime.utcnow()
        )
        db.add(new_user)
        await db.flush()  # Flush to get the user ID

        # Create caregiver profile
        new_caregiver = Caregiver(
            user_id=new_user.id,
            name=full_name,
            phone=phone,
            created_at=datetime.utcnow()
        )
        db.add(new_caregiver)
        
        await db.commit()
        await db.refresh(new_caregiver)
        
        return new_caregiver
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create caregiver: {str(e)}"
        )

@router.get("/available", response_model=List[CaregiverProfileResponse])
async def get_available_caregivers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a list of all available caregivers.
    """
    # Get all active caregivers
    result = await db.execute(
        select(Caregiver)
        .join(User)
        .where(User.is_active == True)
    )
    caregivers = result.scalars().all()
    
    return caregivers

@router.get("/list", response_model=List[CaregiverProfileResponse])
async def list_caregivers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all available caregivers.
    """
    # Get all caregivers
    result = await db.execute(
        select(Caregiver)
        .join(User)
        .where(User.is_active == True)
    )
    caregivers = result.scalars().all()
    
    return caregivers

@router.get("/{caregiver_id}", response_model=CaregiverProfileResponse)
async def get_caregiver(
    caregiver_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific caregiver's profile by ID.
    """
    result = await db.execute(
        select(Caregiver).where(Caregiver.id == caregiver_id)
    )
    caregiver = result.scalar_one_or_none()
    
    if not caregiver:
        raise HTTPException(
            status_code=404,
            detail="Caregiver not found"
        )
    
    return caregiver

@router.delete("/{caregiver_id}")
async def delete_caregiver(
    caregiver_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a caregiver profile. Only the caregiver themselves or an admin can delete the profile.
    """
    result = await db.execute(
        select(Caregiver).where(Caregiver.id == caregiver_id)
    )
    caregiver = result.scalar_one_or_none()
    
    if not caregiver:
        raise HTTPException(
            status_code=404,
            detail="Caregiver not found"
        )
    
    # Check if user has permission to delete
    if current_user.role != UserRoleInput.ADMIN and caregiver.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to delete this caregiver profile"
        )
    
    await db.delete(caregiver)
    await db.commit()
    
    return {"message": "Caregiver profile deleted successfully"}

@router.post("/assign", response_model=CaregiverAssignmentResponse)
async def assign_caregiver(
    request: CaregiverRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Assign a caregiver to a patient. Only primary account holders can make assignments.
    """
    if current_user.role != UserRoleInput.PRIMARY_HOLDER:
        raise HTTPException(
            status_code=403,
            detail="Only Primary Account Holders can assign caregivers"
        )

    # Validate caregiver exists and has CAREGIVER role
    caregiver_result = await db.execute(
        select(User)
        .join(Caregiver)
        .where(User.id == request.user_id)
    )
    caregiver = caregiver_result.scalar_one_or_none()
    if not caregiver or caregiver.role != UserRoleInput.CAREGIVER:
        raise HTTPException(
            status_code=404,
            detail="Caregiver not found or not a valid caregiver"
        )

    # Validate patient exists
    patient_result = await db.execute(
        select(User).where(User.id == request.patient_id)
    )
    patient = patient_result.scalar_one_or_none()
    if not patient:
        raise HTTPException(
            status_code=404,
            detail="Patient not found"
        )

    # Create assignment
    try:
        assignment = CaregiverAssignment(
            caregiver_id=request.user_id,
            patient_id=request.patient_id,
            tasks=request.tasks,
            schedule=request.schedule,
            emergency_contact=request.emergency_contact,
            assigned_at=datetime.utcnow()
        )
        db.add(assignment)
        await db.commit()
        await db.refresh(assignment)
        return assignment
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create assignment: {str(e)}"
        )
