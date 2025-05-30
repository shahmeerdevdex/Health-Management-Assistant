from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

# Valid report types as a constant
VALID_REPORT_TYPES = ["population_health", "patient_outcomes", "operational", "financial", "quality_metrics"]

class ProviderAnalyticsBase(BaseModel):
    report_type: str = Field(..., pattern=f"^({'|'.join(VALID_REPORT_TYPES)})$")
    metrics: Dict[str, Any]
    time_period: str = Field(..., pattern="^(daily|weekly|monthly|quarterly|yearly)$")
    start_date: datetime
    end_date: datetime

class ProviderAnalyticsCreate(ProviderAnalyticsBase):
    pass

class ProviderAnalyticsUpdate(BaseModel):
    report_type: Optional[str] = Field(None, pattern=f"^({'|'.join(VALID_REPORT_TYPES)})$")
    metrics: Optional[Dict[str, Any]] = None
    time_period: Optional[str] = Field(None, pattern="^(daily|weekly|monthly|quarterly|yearly)$")
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class ProviderAnalyticsInDB(ProviderAnalyticsBase):
    id: int
    provider_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PopulationHealthMetricsBase(BaseModel):
    metric_name: str
    value: float
    target_value: Optional[float] = None
    unit: Optional[str] = None
    demographic_breakdown: Optional[Dict] = None
    time_period: str = Field(..., pattern="^(daily|weekly|monthly|quarterly|yearly)$")
    start_date: datetime
    end_date: datetime

class PopulationHealthMetricsCreate(PopulationHealthMetricsBase):
    provider_id: int

class PopulationHealthMetricsUpdate(PopulationHealthMetricsBase):
    pass

class PopulationHealthMetricsResponse(PopulationHealthMetricsBase):
    id: int
    provider_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class QualityMetricsBase(BaseModel):
    metric_name: str
    value: float
    benchmark: Optional[float] = None
    unit: Optional[str] = None
    category: str = Field(..., pattern="^(safety|effectiveness|patient_centered|timeliness|efficiency|equity)$")
    time_period: str = Field(..., pattern="^(daily|weekly|monthly|quarterly|yearly)$")
    start_date: datetime
    end_date: datetime

class QualityMetricsCreate(QualityMetricsBase):
    provider_id: int

class QualityMetricsUpdate(QualityMetricsBase):
    pass

class QualityMetricsResponse(QualityMetricsBase):
    id: int
    provider_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class OperationalMetricsBase(BaseModel):
    metric_name: str
    value: float
    target_value: Optional[float] = None
    unit: Optional[str] = None
    category: str = Field(..., pattern="^(efficiency|capacity|workflow|resource_utilization|patient_flow)$")
    time_period: str = Field(..., pattern="^(daily|weekly|monthly|quarterly|yearly)$")
    start_date: datetime
    end_date: datetime

class OperationalMetricsCreate(OperationalMetricsBase):
    provider_id: int

class OperationalMetricsUpdate(OperationalMetricsBase):
    pass

class OperationalMetricsResponse(OperationalMetricsBase):
    id: int
    provider_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class AnalyticsRequest(BaseModel):
    report_type: str = Field(..., pattern=f"^({'|'.join(VALID_REPORT_TYPES)})$")
    time_period: str = Field(..., pattern="^(daily|weekly|monthly|quarterly|yearly)$")
    start_date: datetime
    end_date: datetime
    metrics: Optional[List[str]] = None
    demographic_filters: Optional[Dict] = None
    category_filters: Optional[List[str]] = None
    provider_id: int

class AnalyticsResponse(BaseModel):
    provider_id: int
    report_type: str
    time_period: str
    start_date: datetime
    end_date: datetime
    metrics: Dict
    summary: Dict
    trends: List[Dict]
    recommendations: List[str] 