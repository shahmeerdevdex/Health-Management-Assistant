from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON, Boolean, Float, Text, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base
from app.schemas.care_plan import TaskFrequency, TaskPriority

class CarePlan(Base):
    __tablename__ = "care_plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    practitioner_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Healthcare provider who created the plan
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=True)  # Null means ongoing
    status = Column(String, default="active")  # active, completed, suspended
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    frequency = Column(Enum(TaskFrequency), nullable=False)  # daily, weekly, biweekly, monthly, custom
    priority = Column(Enum(TaskPriority), nullable=False)  # high, medium, low
    notes = Column(Text, nullable=True)
    
    # Plan components
    medications = Column(JSON, nullable=True)  # List of medications and schedules
    exercises = Column(JSON, nullable=True)  # Exercise routines and schedules
    diet_plan = Column(JSON, nullable=True)  # Dietary recommendations and restrictions
    lifestyle_changes = Column(JSON, nullable=True)  # Lifestyle modifications
    goals = Column(JSON, nullable=True)  # Health goals and milestones
    checkpoints = Column(JSON, nullable=True)  # Progress checkpoints and evaluations
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="care_plans")
    practitioner = relationship("User", foreign_keys=[practitioner_id], back_populates="created_care_plans")
    daily_tasks = relationship("CarePlanDailyTask", back_populates="care_plan", cascade="all, delete-orphan")
    progress_logs = relationship("CarePlanProgress", back_populates="care_plan", cascade="all, delete-orphan")
    exercises = relationship("CarePlanExercise", back_populates="care_plan", cascade="all, delete-orphan")
    diets = relationship("CarePlanDiet", back_populates="care_plan", cascade="all, delete-orphan")
    treatment = relationship("CarePlanTreatment", back_populates="care_plan", cascade="all, delete-orphan", uselist=False)

class CarePlanDailyTask(Base):
    __tablename__ = "care_plan_daily_tasks"

    id = Column(Integer, primary_key=True, index=True)
    care_plan_id = Column(Integer, ForeignKey("care_plans.id"), nullable=False)
    task_type = Column(String, nullable=False)  # medication, exercise, diet, lifestyle
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    scheduled_time = Column(String, nullable=True)  # HH:MM format
    frequency = Column(String, nullable=False)  # daily, weekly, etc.
    days_of_week = Column(JSON, nullable=True)  # For weekly tasks
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    reminder_enabled = Column(Boolean, default=True)
    
    # Relationships
    care_plan = relationship("CarePlan", back_populates="daily_tasks")

class CarePlanProgress(Base):
    __tablename__ = "care_plan_progress"

    id = Column(Integer, primary_key=True, index=True)
    care_plan_id = Column(Integer, ForeignKey("care_plans.id"), nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    metrics = Column(JSON, nullable=False)  # Progress metrics and measurements
    notes = Column(Text, nullable=True)
    completed_tasks = Column(JSON, nullable=True)  # List of completed tasks
    challenges = Column(JSON, nullable=True)  # Challenges faced
    next_steps = Column(JSON, nullable=True)  # Next steps and adjustments
    
    # Relationships
    care_plan = relationship("CarePlan", back_populates="progress_logs")

class CarePlanExercise(Base):
    __tablename__ = "care_plan_exercises"

    id = Column(Integer, primary_key=True, index=True)
    care_plan_id = Column(Integer, ForeignKey("care_plans.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    frequency = Column(String, nullable=False)  # daily, weekly, etc.
    intensity_level = Column(String, nullable=True)  # low, medium, high
    equipment_needed = Column(JSON, nullable=True)  # List of required equipment
    video_url = Column(String, nullable=True)
    instructions = Column(Text, nullable=True)
    precautions = Column(Text, nullable=True)
    target_muscle_groups = Column(JSON, nullable=True)  # List of target muscle groups
    
    # Relationships
    care_plan = relationship("CarePlan", back_populates="exercises")

class CarePlanDiet(Base):
    __tablename__ = "care_plan_diets"

    id = Column(Integer, primary_key=True, index=True)
    care_plan_id = Column(Integer, ForeignKey("care_plans.id"), nullable=False)
    meal_type = Column(String, nullable=False)  # breakfast, lunch, dinner, snack
    time = Column(String, nullable=False)  # HH:MM format
    food_items = Column(JSON, nullable=False)  # List of food items
    portion_sizes = Column(JSON, nullable=True)  # Portion sizes for each food item
    nutritional_info = Column(JSON, nullable=True)  # Calories, macros, etc.
    alternatives = Column(JSON, nullable=True)  # Alternative food options
    restrictions = Column(JSON, nullable=True)  # Dietary restrictions
    notes = Column(Text, nullable=True)
    
    # Relationships
    care_plan = relationship("CarePlan", back_populates="diets")

class CarePlanTreatment(Base):
    __tablename__ = "care_plan_treatments"

    id = Column(Integer, primary_key=True, index=True)
    care_plan_id = Column(Integer, ForeignKey("care_plans.id"), nullable=False)
    diagnosis = Column(Text, nullable=False)
    goals = Column(JSON, nullable=False)  # Treatment goals
    medications = Column(JSON, nullable=True)  # List of medications and schedules
    lifestyle_changes = Column(JSON, nullable=True)  # Required lifestyle modifications
    follow_up_schedule = Column(JSON, nullable=True)  # Follow-up appointments
    risk_factors = Column(JSON, nullable=True)  # Risk factors to monitor
    emergency_contacts = Column(JSON, nullable=True)  # Emergency contact information
    progress_metrics = Column(JSON, nullable=True)  # Metrics to track progress
    
    # Relationships
    care_plan = relationship("CarePlan", back_populates="treatment") 