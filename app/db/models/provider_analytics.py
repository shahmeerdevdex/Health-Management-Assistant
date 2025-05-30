from sqlalchemy import Column, Integer, String, Float, JSON, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.db.base import Base

class ReportType(enum.Enum):
    POPULATION_HEALTH = "population_health"
    PATIENT_OUTCOMES = "patient_outcomes"
    OPERATIONAL = "operational"
    FINANCIAL = "financial"
    QUALITY_METRICS = "quality_metrics"

class ProviderAnalytics(Base):
    """
    Stores provider-level analytics and metrics.
    """
    __tablename__ = "provider_analytics"

    id = Column(Integer, primary_key=True, index=True)
    provider_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    report_type = Column(Enum(ReportType), nullable=False)
    metrics = Column(JSON, nullable=False)  # Stores various metrics and KPIs
    time_period = Column(String, nullable=False)  # e.g., "daily", "weekly", "monthly"
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    provider = relationship("User", back_populates="provider_analytics")

class PopulationHealthMetrics(Base):
    """
    Stores population-level health metrics for providers.
    """
    __tablename__ = "population_health_metrics"

    id = Column(Integer, primary_key=True, index=True)
    provider_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    metric_name = Column(String, nullable=False)  # e.g., "diabetes_prevalence", "vaccination_rate"
    value = Column(Float, nullable=False)
    target_value = Column(Float, nullable=True)
    unit = Column(String, nullable=True)  # e.g., "percentage", "count"
    demographic_breakdown = Column(JSON, nullable=True)  # Age groups, gender, etc.
    time_period = Column(String, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    provider = relationship("User", back_populates="population_health_metrics")

class QualityMetrics(Base):
    """
    Stores healthcare quality metrics for providers.
    """
    __tablename__ = "quality_metrics"

    id = Column(Integer, primary_key=True, index=True)
    provider_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    metric_name = Column(String, nullable=False)  # e.g., "readmission_rate", "patient_satisfaction"
    value = Column(Float, nullable=False)
    benchmark = Column(Float, nullable=True)
    unit = Column(String, nullable=True)
    category = Column(String, nullable=False)  # e.g., "safety", "effectiveness", "patient_centered"
    time_period = Column(String, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    provider = relationship("User", back_populates="quality_metrics")

class OperationalMetrics(Base):
    """
    Stores operational metrics for healthcare providers.
    """
    __tablename__ = "operational_metrics"

    id = Column(Integer, primary_key=True, index=True)
    provider_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    metric_name = Column(String, nullable=False)  # e.g., "appointment_utilization", "wait_time"
    value = Column(Float, nullable=False)
    target_value = Column(Float, nullable=True)
    unit = Column(String, nullable=True)
    category = Column(String, nullable=False)  # e.g., "efficiency", "capacity", "workflow"
    time_period = Column(String, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    provider = relationship("User", back_populates="operational_metrics") 