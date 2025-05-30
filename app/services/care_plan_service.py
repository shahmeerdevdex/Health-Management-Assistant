from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from app.db.models.care_plan import (
    CarePlan,
    CarePlanDailyTask,
    CarePlanProgress,
    CarePlanExercise,
    CarePlanDiet,
    CarePlanTreatment
)
from app.schemas.care_plan import (
    CarePlanCreate,
    CarePlanUpdate,
    DailyChecklistItem,
    ExerciseRoutine,
    DietPlan,
    TreatmentPlan,
    ProgressLogCreate,
    DailyTaskCreate,
    DailyTaskUpdate
)
from app.services.notification_service import send_notification
import logging

logger = logging.getLogger(__name__)

from datetime import datetime
from typing import Optional

def make_naive(dt: Optional[datetime]) -> Optional[datetime]:
    """Converts timezone-aware datetime to naive (UTC-based) for DB insertion."""
    if dt and dt.tzinfo is not None:
        return dt.replace(tzinfo=None)
    return dt

def serialize_datetime(obj):
    """Helper function to serialize datetime objects to ISO format strings."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {key: serialize_datetime(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [serialize_datetime(item) for item in obj]
    return obj

async def create_care_plan(db: AsyncSession, plan_data: CarePlanCreate) -> Dict[str, Any]:
    """Create a new comprehensive care plan with all components."""
    try:
        # Create main care plan with tz-naive datetimes
        care_plan = CarePlan(
            user_id=plan_data.user_id,
            title=plan_data.title,
            description=plan_data.description,
            start_date=make_naive(plan_data.start_date),
            end_date=make_naive(plan_data.end_date),
            frequency=plan_data.frequency,
            priority=plan_data.priority,
            notes=plan_data.notes,
            practitioner_id=plan_data.practitioner_id,
            status='active'  # Set default status
        )
        db.add(care_plan)
        await db.flush()  # Get the care_plan.id

        # Create daily checklist items
        daily_tasks = []
        for item in plan_data.daily_checklist:
            task = CarePlanDailyTask(
                care_plan_id=care_plan.id,
                task_type=item.category.value,
                title=item.title,
                description=item.description,
                frequency='daily',  # Set default frequency
                is_completed=False,  # Set default completion status
                reminder_enabled=True  # Enable reminders by default
            )
            db.add(task)
            await db.flush()  # Get the task.id
            daily_tasks.append({
                'task_id': task.id,
                'category': item.category,
                'title': task.title,
                'description': task.description,
                'priority': item.priority,
                'time_slots': item.time_slots,
                'is_completed': task.is_completed,
                'completed_at': task.completed_at
            })

        # Create exercise routines
        exercises = []
        for routine in plan_data.exercise_routines:
            exercise = CarePlanExercise(
                care_plan_id=care_plan.id,
                name=routine.name,
                description=routine.description,
                duration_minutes=routine.duration_minutes,
                frequency=routine.frequency.value if hasattr(routine.frequency, 'value') else routine.frequency,
                intensity_level=str(routine.intensity_level),  # Convert to string
                equipment_needed=routine.equipment_needed,
                video_url=routine.video_url,
                instructions=','.join(routine.instructions) if isinstance(routine.instructions, list) else routine.instructions,
                precautions=','.join(routine.precautions) if isinstance(routine.precautions, list) else routine.precautions,
                target_muscle_groups=routine.target_muscle_groups
            )
            db.add(exercise)
            await db.flush()  # Get the exercise.id
            exercises.append({
                'id': exercise.id,
                'name': exercise.name,
                'description': exercise.description,
                'duration_minutes': exercise.duration_minutes,
                'frequency': exercise.frequency,
                'intensity_level': exercise.intensity_level,
                'equipment_needed': exercise.equipment_needed,
                'video_url': exercise.video_url,
                'instructions': routine.instructions if isinstance(routine.instructions, list) else [routine.instructions],
                'precautions': routine.precautions if isinstance(routine.precautions, list) else [routine.precautions],
                'target_muscle_groups': exercise.target_muscle_groups
            })

        # Create diet plan
        diets = []
        for meal in plan_data.diet_plan:
            # Convert time to string format (HH:MM:SS)
            time_str = meal.time.strftime('%H:%M:%S') if meal.time else None
            
            diet = CarePlanDiet(
                care_plan_id=care_plan.id,
                meal_type=meal.meal_type,
                time=time_str,
                food_items=meal.food_items,
                portion_sizes=meal.portion_sizes,
                nutritional_info=meal.nutritional_info,
                alternatives=meal.alternatives,
                restrictions=meal.restrictions,
                notes=meal.notes
            )
            db.add(diet)
            await db.flush()  # Get the diet.id
            diets.append({
                'id': diet.id,
                'meal_type': diet.meal_type,
                'time': diet.time,
                'food_items': diet.food_items,
                'portion_sizes': diet.portion_sizes,
                'nutritional_info': diet.nutritional_info,
                'alternatives': diet.alternatives,
                'restrictions': diet.restrictions,
                'notes': diet.notes
            })

        # Create treatment plan with serialized datetime objects
        treatment = CarePlanTreatment(
            care_plan_id=care_plan.id,
            diagnosis=plan_data.treatment_plan.diagnosis,
            goals=serialize_datetime(plan_data.treatment_plan.goals),
            medications=serialize_datetime(plan_data.treatment_plan.medications),
            lifestyle_changes=serialize_datetime(plan_data.treatment_plan.lifestyle_changes),
            follow_up_schedule=serialize_datetime(plan_data.treatment_plan.follow_up_schedule),
            risk_factors=serialize_datetime(plan_data.treatment_plan.risk_factors),
            emergency_contacts=serialize_datetime(plan_data.treatment_plan.emergency_contacts),
            progress_metrics=serialize_datetime(plan_data.treatment_plan.progress_metrics)
        )
        db.add(treatment)
        await db.flush()  # Get the treatment.id

        await db.commit()
        await db.refresh(care_plan)

        # Calculate completion rate
        total_tasks = len(daily_tasks)
        completed_tasks = sum(1 for task in daily_tasks if task['is_completed'])
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

        # Return the complete response
        return {
            "id": care_plan.id,
            "user_id": care_plan.user_id,
            "title": care_plan.title,
            "description": care_plan.description,
            "start_date": care_plan.start_date,
            "end_date": care_plan.end_date,
            "frequency": care_plan.frequency,
            "priority": care_plan.priority,
            "notes": care_plan.notes,
            "practitioner_id": care_plan.practitioner_id,
            "created_at": care_plan.created_at,
            "updated_at": care_plan.updated_at,
            "status": care_plan.status,
            "daily_checklist": daily_tasks,
            "exercise_routines": exercises,
            "diet_plan": diets,
            "treatment_plan": {
                "id": treatment.id,
                "diagnosis": treatment.diagnosis,
                "goals": treatment.goals,
                "medications": treatment.medications,
                "lifestyle_changes": treatment.lifestyle_changes,
                "follow_up_schedule": treatment.follow_up_schedule,
                "risk_factors": treatment.risk_factors,
                "emergency_contacts": treatment.emergency_contacts,
                "progress_metrics": treatment.progress_metrics
            },
            "completion_rate": completion_rate
        }

    except Exception as e:
        await db.rollback()
        raise e

async def get_user_care_plans(
    db: AsyncSession,
    user_id: int,
    status: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Get all care plans for a user with optional status filter."""
    # Build the base query
    query = select(CarePlan).where(CarePlan.user_id == user_id)
    if status:
        query = query.where(CarePlan.status == status)
    
    # Execute the query
    result = await db.execute(query)
    care_plans = result.scalars().all()
    
    # Format the response for each care plan
    formatted_plans = []
    for plan in care_plans:
        # Get daily tasks
        tasks_query = select(CarePlanDailyTask).where(CarePlanDailyTask.care_plan_id == plan.id)
        tasks_result = await db.execute(tasks_query)
        daily_tasks = []
        for task in tasks_result.scalars().all():
            daily_tasks.append({
                'task_id': task.id,
                'category': task.task_type,
                'title': task.title,
                'description': task.description,
                'priority': plan.priority,
                'time_slots': [],  # Default empty list since it's not stored
                'is_completed': task.is_completed,
                'completed_at': task.completed_at
            })

        # Get exercise routines
        exercises_query = select(CarePlanExercise).where(CarePlanExercise.care_plan_id == plan.id)
        exercises_result = await db.execute(exercises_query)
        exercises = []
        for exercise in exercises_result.scalars().all():
            exercises.append({
                'id': exercise.id,
                'name': exercise.name,
                'description': exercise.description,
                'duration_minutes': exercise.duration_minutes,
                'frequency': exercise.frequency,
                'intensity_level': exercise.intensity_level,
                'equipment_needed': exercise.equipment_needed,
                'video_url': exercise.video_url,
                'instructions': exercise.instructions.split(',') if exercise.instructions else [],
                'precautions': exercise.precautions.split(',') if exercise.precautions else [],
                'target_muscle_groups': exercise.target_muscle_groups
            })

        # Get diet plan
        diets_query = select(CarePlanDiet).where(CarePlanDiet.care_plan_id == plan.id)
        diets_result = await db.execute(diets_query)
        diets = []
        for diet in diets_result.scalars().all():
            diets.append({
                'id': diet.id,
                'meal_type': diet.meal_type,
                'time': diet.time,
                'food_items': diet.food_items,
                'portion_sizes': diet.portion_sizes,
                'nutritional_info': diet.nutritional_info,
                'alternatives': diet.alternatives,
                'restrictions': diet.restrictions,
                'notes': diet.notes
            })

        # Get treatment plan
        treatment_query = select(CarePlanTreatment).where(CarePlanTreatment.care_plan_id == plan.id)
        treatment_result = await db.execute(treatment_query)
        treatment = treatment_result.scalar_one_or_none()
        
        # Calculate completion rate
        total_tasks = len(daily_tasks)
        completed_tasks = sum(1 for task in daily_tasks if task['is_completed'])
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

        # Format the complete care plan
        formatted_plan = {
            "id": plan.id,
            "user_id": plan.user_id,
            "title": plan.title,
            "description": plan.description,
            "start_date": plan.start_date,
            "end_date": plan.end_date,
            "frequency": plan.frequency,
            "priority": plan.priority,
            "notes": plan.notes,
            "practitioner_id": plan.practitioner_id,
            "created_at": plan.created_at,
            "updated_at": plan.updated_at,
            "status": plan.status,
            "daily_checklist": daily_tasks,
            "exercise_routines": exercises,
            "diet_plan": diets,
            "treatment_plan": {
                "id": treatment.id if treatment else None,
                "diagnosis": treatment.diagnosis if treatment else None,
                "goals": treatment.goals if treatment else [],
                "medications": treatment.medications if treatment else [],
                "lifestyle_changes": treatment.lifestyle_changes if treatment else [],
                "follow_up_schedule": treatment.follow_up_schedule if treatment else [],
                "risk_factors": treatment.risk_factors if treatment else [],
                "emergency_contacts": treatment.emergency_contacts if treatment else [],
                "progress_metrics": treatment.progress_metrics if treatment else []
            },
            "completion_rate": completion_rate
        }
        formatted_plans.append(formatted_plan)

    return formatted_plans

async def get_care_plan_summary(db: AsyncSession, plan_id: int) -> Dict[str, Any]:
    """
    Get a summary of a specific care plan.
    """
    try:
        # Get care plan
        query = select(CarePlan).where(CarePlan.id == plan_id)
        result = await db.execute(query)
        plan = result.scalar_one_or_none()
        
        if not plan:
            raise ValueError("Care plan not found")

        # Get daily tasks
        tasks_query = select(CarePlanDailyTask).where(CarePlanDailyTask.care_plan_id == plan_id)
        tasks_result = await db.execute(tasks_query)
        tasks = tasks_result.scalars().all()
        
        # Get progress logs
        progress_query = select(CarePlanProgress).where(CarePlanProgress.care_plan_id == plan_id)
        progress_result = await db.execute(progress_query)
        progress_logs = progress_result.scalars().all()

        # Get upcoming exercises
        exercises_query = select(CarePlanExercise).where(CarePlanExercise.care_plan_id == plan_id)
        exercises_result = await db.execute(exercises_query)
        upcoming_exercises = exercises_result.scalars().all()

        # Get next meals - convert current time to string format for comparison
        current_time = datetime.now().time().strftime('%H:%M:%S')
        meals_query = select(CarePlanDiet).where(
            and_(
                CarePlanDiet.care_plan_id == plan_id,
                CarePlanDiet.time > current_time
            )
        ).order_by(CarePlanDiet.time)
        meals_result = await db.execute(meals_query)
        next_meals = meals_result.scalars().all()

        # Calculate completion rate
        completion_rate = sum(1 for task in tasks if task.is_completed) / len(tasks) if tasks else 0
        
        # Get treatment plan
        treatment_query = select(CarePlanTreatment).where(CarePlanTreatment.care_plan_id == plan_id)
        treatment_result = await db.execute(treatment_query)
        treatment = treatment_result.scalar_one_or_none()

        return {
            'id': plan.id,
            'title': plan.title,
            'start_date': plan.start_date,
            'end_date': plan.end_date,
            'status': plan.status,
            'completion_rate': completion_rate,
            'total_tasks': len(tasks),
            'completed_tasks': sum(1 for task in tasks if task.is_completed),
            'next_tasks': [{
                'task_id': task.id,
                'category': task.task_type,
                'title': task.title,
                'description': task.description,
                'priority': plan.priority,
                'time_slots': [],  # Default empty list since it's not stored
                'is_completed': task.is_completed,
                'completed_at': task.completed_at
            } for task in tasks if not task.is_completed],
            'upcoming_exercises': [{
                'id': ex.id,
                'name': ex.name,
                'description': ex.description,
                'duration_minutes': ex.duration_minutes,
                'frequency': ex.frequency,
                'intensity_level': ex.intensity_level,
                'instructions': ex.instructions.split(',') if ex.instructions else [],
                'precautions': ex.precautions.split(',') if ex.precautions else [],
                'target_muscle_groups': ex.target_muscle_groups
            } for ex in upcoming_exercises],
            'next_meals': [{
                'id': meal.id,
                'meal_type': meal.meal_type,
                'time': meal.time,
                'food_items': meal.food_items,
                'portion_sizes': meal.portion_sizes,
                'nutritional_info': meal.nutritional_info,
                'alternatives': meal.alternatives,
                'restrictions': meal.restrictions,
                'notes': meal.notes
            } for meal in next_meals],
            'treatment_progress': {
                'goals': treatment.goals if treatment else [],
                'medications': treatment.medications if treatment else [],
                'follow_up_schedule': treatment.follow_up_schedule if treatment else []
            } if treatment else None,
            'progress_logs': [{
                'id': log.id,
                'date': log.date,
                'notes': log.notes,
                'metrics': log.metrics
            } for log in progress_logs]
        }
    except Exception as e:
        raise Exception(f"Failed to get care plan summary: {str(e)}")

async def update_task_status(
    db: AsyncSession,
    task_id: int,
    task_data: DailyTaskUpdate
) -> Dict[str, Any]:
    """Update a daily task with all provided fields."""
    task_query = select(CarePlanDailyTask).where(CarePlanDailyTask.id == task_id)
    task_result = await db.execute(task_query)
    task = task_result.scalar_one_or_none()
    
    if not task:
        raise ValueError("Task not found")
    
    # Update all provided fields
    if task_data.task_type is not None:
        task.task_type = task_data.task_type
    if task_data.title is not None:
        task.title = task_data.title
    if task_data.description is not None:
        task.description = task_data.description
    if task_data.scheduled_time is not None:
        task.scheduled_time = task_data.scheduled_time
    if task_data.frequency is not None:
        task.frequency = task_data.frequency
    if task_data.days_of_week is not None:
        task.days_of_week = task_data.days_of_week
    if task_data.reminder_enabled is not None:
        task.reminder_enabled = task_data.reminder_enabled
    if task_data.is_completed is not None:
        task.is_completed = task_data.is_completed
        task.completed_at = datetime.utcnow() if task_data.is_completed else None
    
    await db.commit()
    await db.refresh(task)
    
    return {
        'id': task.id,
        'care_plan_id': task.care_plan_id,
        'task_type': task.task_type,
        'title': task.title,
        'description': task.description,
        'scheduled_time': task.scheduled_time,
        'frequency': task.frequency,
        'days_of_week': task.days_of_week,
        'reminder_enabled': task.reminder_enabled,
        'is_completed': task.is_completed,
        'completed_at': task.completed_at
    }

async def log_progress(
    db: AsyncSession,
    progress_data: ProgressLogCreate
) -> Dict[str, Any]:
    """Log progress for a care plan."""
    try:
        # Format the metrics data
        metrics = {
            'exercise_completion': progress_data.exercise_completion,
            'diet_adherence': progress_data.diet_adherence,
            'vital_signs': progress_data.vital_signs,
            'symptoms': progress_data.symptoms,
            'mood_rating': progress_data.mood_rating
        }

        progress = CarePlanProgress(
            care_plan_id=progress_data.care_plan_id,
            date=make_naive(progress_data.date),  # Convert to naive datetime
            metrics=metrics,
            notes=progress_data.notes,
            completed_tasks=progress_data.completed_tasks
        )
        
        db.add(progress)
        await db.commit()
        await db.refresh(progress)

        # Flatten the metrics in the response
        return {
            'id': progress.id,
            'care_plan_id': progress.care_plan_id,
            'date': progress.date,
            'exercise_completion': progress.metrics['exercise_completion'],
            'diet_adherence': progress.metrics['diet_adherence'],
            'vital_signs': progress.metrics['vital_signs'],
            'symptoms': progress.metrics['symptoms'],
            'mood_rating': progress.metrics['mood_rating'],
            'notes': progress.notes,
            'completed_tasks': progress.completed_tasks,
            'created_at': datetime.utcnow()  # Add created_at field
        }
    except Exception as e:
        await db.rollback()
        raise Exception(f"Failed to log progress: {str(e)}")

async def create_daily_task(db: AsyncSession, task_data: DailyTaskCreate) -> Dict[str, Any]:
    """
    Create a new daily task for a care plan.
    """
    try:
        # Create the task
        task = CarePlanDailyTask(
            care_plan_id=task_data.care_plan_id,
            task_type=task_data.task_type,
            title=task_data.title,
            description=task_data.description,
            frequency=task_data.frequency,
            is_completed=False,
            reminder_enabled=task_data.reminder_enabled
        )
        db.add(task)
        await db.flush()

        # Get the associated care plan for priority
        plan_query = select(CarePlan).where(CarePlan.id == task_data.care_plan_id)
        plan_result = await db.execute(plan_query)
        plan = plan_result.scalar_one()

        # Commit the changes
        await db.commit()
        await db.refresh(task)

        return {
            'id': task.id,
            'care_plan_id': task.care_plan_id,
            'task_type': task.task_type,
            'title': task.title,
            'description': task.description,
            'scheduled_time': task_data.scheduled_time,
            'frequency': task.frequency,
            'days_of_week': task_data.days_of_week,
            'reminder_enabled': task.reminder_enabled,
            'is_completed': task.is_completed,
            'completed_at': task.completed_at
        }
    except Exception as e:
        await db.rollback()
        raise Exception(f"Failed to create daily task: {str(e)}") 