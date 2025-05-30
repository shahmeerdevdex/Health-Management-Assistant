from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, time
from enum import Enum

class TaskFrequency(str, Enum):
    daily = "daily"
    weekly = "weekly"
    biweekly = "biweekly"
    monthly = "monthly"
    custom = "custom"

class TaskPriority(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"

class TaskCategory(str, Enum):
    MEDICATION = "medication"
    EXERCISE = "exercise"
    DIET = "diet"
    MENTAL_HEALTH = "mental_health"
    VITAL_SIGNS = "vital_signs"
    OTHER = "other"

class TimeSlot(BaseModel):
    start_time: time
    end_time: time
    description: Optional[str] = None

class DailyChecklistItem(BaseModel):
    task_id: int
    title: str
    description: Optional[str]
    category: TaskCategory
    priority: TaskPriority
    time_slots: List[TimeSlot]
    is_completed: bool = False
    notes: Optional[str] = None

class ExerciseRoutine(BaseModel):
    name: str
    description: str
    duration_minutes: int
    frequency: TaskFrequency
    intensity_level: int = Field(ge=1, le=5)
    equipment_needed: Optional[List[str]] = None
    video_url: Optional[str] = None
    instructions: List[str]
    precautions: Optional[List[str]] = None
    target_muscle_groups: Optional[List[str]] = None

class DietPlan(BaseModel):
    meal_type: str  # breakfast, lunch, dinner, snack
    time: time
    food_items: List[str]
    portion_sizes: Dict[str, str]
    nutritional_info: Dict[str, float]
    alternatives: Optional[List[str]] = None
    restrictions: Optional[List[str]] = None
    notes: Optional[str] = None

class TreatmentPlan(BaseModel):
    diagnosis: str
    goals: List[str]
    medications: List[Dict[str, Any]]
    lifestyle_changes: List[str]
    follow_up_schedule: List[datetime]
    risk_factors: List[str]
    emergency_contacts: List[Dict[str, str]]
    progress_metrics: List[str]

class CarePlanBase(BaseModel):
    title: str
    description: Optional[str] = None
    start_date: datetime
    end_date: Optional[datetime] = None
    daily_checklist: List[DailyChecklistItem]
    exercise_routines: List[ExerciseRoutine]
    diet_plan: List[DietPlan]
    treatment_plan: TreatmentPlan
    frequency: TaskFrequency
    priority: TaskPriority
    notes: Optional[str] = None

class CarePlanCreate(BaseModel):
    user_id: int
    title: str
    description: str
    start_date: datetime
    end_date: Optional[datetime] = None
    daily_checklist: List[DailyChecklistItem]
    exercise_routines: List[ExerciseRoutine]
    diet_plan: List[DietPlan]
    treatment_plan: TreatmentPlan
    frequency: TaskFrequency
    priority: TaskPriority
    notes: Optional[str] = None
    practitioner_id: Optional[int] = None

class CarePlanUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    end_date: Optional[datetime] = None
    daily_checklist: Optional[List[DailyChecklistItem]] = None
    exercise_routines: Optional[List[ExerciseRoutine]] = None
    diet_plan: Optional[List[DietPlan]] = None
    treatment_plan: Optional[TreatmentPlan] = None
    frequency: Optional[TaskFrequency] = None
    priority: Optional[TaskPriority] = None
    notes: Optional[str] = None

class CarePlanResponse(BaseModel):
    id: int
    user_id: int
    title: str
    description: str
    start_date: datetime
    end_date: Optional[datetime]
    daily_checklist: List[DailyChecklistItem]
    exercise_routines: List[ExerciseRoutine]
    diet_plan: List[DietPlan]
    treatment_plan: TreatmentPlan
    frequency: TaskFrequency
    priority: TaskPriority
    notes: Optional[str]
    practitioner_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    completion_rate: float
    status: str

    class Config:
        from_attributes = True

class DailyTaskBase(BaseModel):
    task_type: str = Field(..., pattern="^(medication|exercise|diet|lifestyle)$")
    title: str
    description: Optional[str] = None
    scheduled_time: Optional[str] = Field(None, pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    frequency: str = Field(..., pattern="^(daily|weekly|biweekly|monthly)$")
    days_of_week: Optional[List[str]] = None
    reminder_enabled: bool = True

class DailyTaskCreate(DailyTaskBase):
    care_plan_id: int

class DailyTaskUpdate(DailyTaskBase):
    is_completed: Optional[bool] = None
    completed_at: Optional[datetime] = None

class DailyTaskResponse(DailyTaskBase):
    id: int
    care_plan_id: int
    is_completed: bool
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True

class ProgressLogBase(BaseModel):
    metrics: Dict
    notes: Optional[str] = None
    completed_tasks: Optional[List[Dict]] = None
    challenges: Optional[List[str]] = None
    next_steps: Optional[List[str]] = None

class ProgressLogCreate(BaseModel):
    care_plan_id: int
    date: datetime
    completed_tasks: List[int]
    exercise_completion: Dict[str, bool]
    diet_adherence: Dict[str, bool]
    vital_signs: Optional[Dict[str, float]] = None
    symptoms: Optional[List[str]] = None
    notes: Optional[str] = None
    mood_rating: Optional[int] = Field(None, ge=1, le=5)

class ProgressLogResponse(BaseModel):
    id: int
    care_plan_id: int
    date: datetime
    completed_tasks: List[int]
    exercise_completion: Dict[str, bool]
    diet_adherence: Dict[str, bool]
    vital_signs: Optional[Dict[str, float]]
    symptoms: Optional[List[str]]
    notes: Optional[str]
    mood_rating: Optional[int]
    created_at: datetime

class CarePlanSummary(BaseModel):
    id: int
    title: str
    start_date: datetime
    end_date: Optional[datetime]
    completion_rate: float
    next_tasks: List[DailyChecklistItem]
    upcoming_exercises: List[ExerciseRoutine]
    next_meals: List[DietPlan]
    treatment_progress: Dict[str, Any]
    status: str

    class Config:
        from_attributes = True 