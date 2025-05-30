from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.api.endpoints.dependencies import get_db, get_current_user
from app.schemas.care_plan import (
    CarePlanCreate,
    CarePlanResponse,
    CarePlanUpdate,
    DailyTaskCreate,
    DailyTaskResponse,
    DailyTaskUpdate,
    ProgressLogCreate,
    ProgressLogResponse,
    CarePlanSummary
)
from app.services.care_plan_service import (
    create_care_plan,
    get_user_care_plans,
    get_care_plan_summary,
    update_task_status,
    log_progress,
    create_daily_task
)
from app.db.models.user import User, UserRoleInput
from app.db.models.care_plan import CarePlan, CarePlanDailyTask
from sqlalchemy import select
from pydantic import validator

router = APIRouter()

@router.post("/", response_model=CarePlanResponse)
async def create_new_care_plan(
    plan_data: CarePlanCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new care plan.
    """
    if plan_data.user_id != current_user.id and current_user.role != UserRoleInput.PRACTITIONER:
        raise HTTPException(status_code=403, detail="Not authorized to create care plan for another user")
    
    try:
        care_plan = await create_care_plan(db, plan_data)
        return care_plan
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[CarePlanResponse])
async def list_care_plans(
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all care plans for the current user.
    """
    try:
        plans = await get_user_care_plans(db, current_user.id, status)
        return plans
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{plan_id}/summary", response_model=CarePlanSummary)
async def get_plan_summary(
    plan_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a summary of a specific care plan.
    """
    # Check if user has access to the care plan
    query = select(CarePlan).where(
        CarePlan.id == plan_id,
        (CarePlan.user_id == current_user.id) | (CarePlan.practitioner_id == current_user.id)
    )
    result = await db.execute(query)
    plan = result.scalar_one_or_none()
    
    if not plan:
        raise HTTPException(status_code=404, detail="Care plan not found or access denied")
    
    try:
        summary = await get_care_plan_summary(db, plan_id)
        return summary
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{plan_id}/tasks", response_model=DailyTaskResponse)
async def create_daily_task_endpoint(
    plan_id: int,
    task_data: DailyTaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Add a new daily task to a care plan.
    """
    # Check if user has access to the care plan
    query = select(CarePlan).where(
        CarePlan.id == plan_id,
        (CarePlan.user_id == current_user.id) | (CarePlan.practitioner_id == current_user.id)
    )
    result = await db.execute(query)
    plan = result.scalar_one_or_none()
    
    if not plan:
        raise HTTPException(status_code=404, detail="Care plan not found or access denied")
    
    if task_data.care_plan_id != plan_id:
        raise HTTPException(status_code=400, detail="Task plan ID mismatch")
    
    try:
        task = await create_daily_task(db, task_data)
        return task
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/tasks/{task_id}", response_model=DailyTaskResponse)
async def update_task(
    task_id: int,
    task_data: DailyTaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a daily task.
    """
    # Check if user has access to the task
    query = select(CarePlanDailyTask).join(CarePlan).where(
        CarePlanDailyTask.id == task_id,
        (CarePlan.user_id == current_user.id) | (CarePlan.practitioner_id == current_user.id)
    )
    result = await db.execute(query)
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found or access denied")
    
    try:
        updated_task = await update_task_status(db, task_id, task_data)
        return updated_task
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{plan_id}/progress", response_model=ProgressLogResponse)
async def add_progress_log(
    plan_id: int,
    progress_data: ProgressLogCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Log progress for a care plan.
    """
    # Check if user has access to the care plan
    query = select(CarePlan).where(
        CarePlan.id == plan_id,
        (CarePlan.user_id == current_user.id) | (CarePlan.practitioner_id == current_user.id)
    )
    result = await db.execute(query)
    plan = result.scalar_one_or_none()
    
    if not plan:
        raise HTTPException(status_code=404, detail="Care plan not found or access denied")
    
    if progress_data.care_plan_id != plan_id:
        raise HTTPException(status_code=400, detail="Progress plan ID mismatch")
    
    try:
        progress = await log_progress(db, progress_data)
        return progress
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class CarePlanCreate(CarePlanCreate):
    @validator('frequency', pre=True)
    def frequency_to_lower(cls, v):
        if isinstance(v, str):
            return v.lower()
        return v

    @validator('priority', pre=True)
    def priority_to_lower(cls, v):
        if isinstance(v, str):
            return v.lower()
        return v 