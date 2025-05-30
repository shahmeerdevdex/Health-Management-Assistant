from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict
from datetime import datetime, timezone
from app.api.endpoints.dependencies import get_db, get_current_user
from app.schemas.provider_analytics import (
    ProviderAnalyticsCreate,
    ProviderAnalyticsUpdate,
    ProviderAnalyticsInDB,
    VALID_REPORT_TYPES,
    PopulationHealthMetricsCreate,
    PopulationHealthMetricsResponse,
    QualityMetricsCreate,
    QualityMetricsResponse
)

from app.services.provider_analytics_service import (
    create_provider_analytics,
    get_provider_analytics,
    create_population_health_metrics,
    get_population_health_metrics,
    create_quality_metrics,
    get_quality_metrics,
    
)

from app.db.models.user import User, UserRoleInput
from app.db.models.provider_analytics import ProviderAnalytics, ReportType
from sqlalchemy.future import select
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

def ensure_naive_utc(dt: datetime) -> datetime:
    """Convert datetime to naive UTC."""
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc)
        dt = dt.replace(tzinfo=None)
    return dt

@router.post("/analytics", response_model=ProviderAnalyticsInDB)
async def create_provider_analytics(
    *,
    db: AsyncSession = Depends(get_db),
    analytics_in: ProviderAnalyticsCreate,
    current_user: User = Depends(get_current_user)
):
    """Create new provider analytics."""
    if current_user.role not in [UserRoleInput.PRACTITIONER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only practitioners can create analytics"
        )

    try:
        # Convert all datetimes to naive UTC
        start_date = ensure_naive_utc(analytics_in.start_date)
        end_date = ensure_naive_utc(analytics_in.end_date)
        now = ensure_naive_utc(datetime.now(timezone.utc))

        # Convert string report type to enum
        try:
            report_type_enum = ReportType[analytics_in.report_type.upper()]
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid report type. Must be one of: {', '.join(VALID_REPORT_TYPES)}"
            )

        analytics = ProviderAnalytics(
            provider_id=current_user.id,
            report_type=report_type_enum,
            metrics=analytics_in.metrics,
            time_period=analytics_in.time_period,
            start_date=start_date,
            end_date=end_date,
            created_at=now,
            updated_at=now
        )
        db.add(analytics)
        await db.commit()
        await db.refresh(analytics)

        return analytics

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating analytics: {str(e)}"
        )

@router.get("/analytics/{provider_id}", response_model=List[ProviderAnalyticsInDB])
async def get_provider_analytics(
    provider_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get analytics for a provider."""
    try:
        # Check authorization
        if current_user.role not in [UserRoleInput.PRACTITIONER, UserRoleInput.ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view provider analytics"
            )

        # If not admin, can only view own analytics
        if current_user.role == UserRoleInput.PRACTITIONER and current_user.id != provider_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only view own analytics"
            )

        # Get analytics
        result = await db.execute(
            select(ProviderAnalytics).where(
                ProviderAnalytics.provider_id == provider_id
            )
        )
        analytics = result.scalars().all()

        return analytics
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error getting provider analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.put("/analytics/{analytics_id}", response_model=ProviderAnalyticsInDB)
async def update_provider_analytics(
    *,
    db: AsyncSession = Depends(get_db),
    analytics_id: int,
    analytics_in: ProviderAnalyticsUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update provider analytics."""
    try:
        # Get analytics record
        result = await db.execute(
            select(ProviderAnalytics).where(
                ProviderAnalytics.id == analytics_id
            )
        )
        analytics = result.scalars().first()

        if not analytics:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analytics record not found"
            )

        # Check authorization
        if current_user.role != UserRoleInput.PRACTITIONER or current_user.id != analytics.provider_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update these analytics"
            )

        # Update analytics with proper timezone handling
        update_data = analytics_in.dict(exclude_unset=True)
        
        # Convert report type to enum if provided
        if "report_type" in update_data:
            try:
                update_data["report_type"] = ReportType[update_data["report_type"].upper()]
            except KeyError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid report type. Must be one of: {', '.join(VALID_REPORT_TYPES)}"
                )

        # Convert datetime fields to naive UTC if provided
        if "start_date" in update_data:
            update_data["start_date"] = ensure_naive_utc(update_data["start_date"])
        if "end_date" in update_data:
            update_data["end_date"] = ensure_naive_utc(update_data["end_date"])

        # Update the record
        for field, value in update_data.items():
            setattr(analytics, field, value)
        
        analytics.updated_at = ensure_naive_utc(datetime.now(timezone.utc))

        await db.commit()
        await db.refresh(analytics)

        return analytics
    except HTTPException as e:
        raise e
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating provider analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/population-health", response_model=PopulationHealthMetricsResponse)
async def create_population_health(
    metrics_data: PopulationHealthMetricsCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create new population health metrics."""
    if current_user.role != UserRoleInput.PRACTITIONER:
        raise HTTPException(status_code=403, detail="Only practitioners can create population health metrics")
    
    try:
        # Convert datetime fields to naive UTC
        metrics_data_dict = metrics_data.dict()
        metrics_data_dict["start_date"] = ensure_naive_utc(metrics_data.start_date)
        metrics_data_dict["end_date"] = ensure_naive_utc(metrics_data.end_date)
        
        # Create metrics with naive UTC datetimes
        metrics = await create_population_health_metrics(db, PopulationHealthMetricsCreate(**metrics_data_dict))
        return metrics
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating population health metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/population-health", response_model=List[PopulationHealthMetricsResponse])
async def get_population_health(
    time_period: str,
    start_date: datetime,
    end_date: datetime,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get population health metrics for a specific time period."""
    if current_user.role != UserRoleInput.PRACTITIONER:
        raise HTTPException(status_code=403, detail="Only practitioners can view population health metrics")
    
    try:
        # Convert datetime fields to naive UTC
        start_date = ensure_naive_utc(start_date)
        end_date = ensure_naive_utc(end_date)
        
        metrics = await get_population_health_metrics(
            db, current_user.id, time_period, start_date, end_date
        )
        return metrics
    except Exception as e:
        logger.error(f"Error getting population health metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/quality-metrics", response_model=QualityMetricsResponse)
async def create_quality_metrics_endpoint(
    metrics_data: QualityMetricsCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create new quality metrics."""
    try:
        # Convert datetime fields to naive UTC
        metrics_data_dict = metrics_data.dict()
        metrics_data_dict["start_date"] = ensure_naive_utc(metrics_data.start_date)
        metrics_data_dict["end_date"] = ensure_naive_utc(metrics_data.end_date)
        
        # Create metrics with naive UTC datetimes
        metrics = await create_quality_metrics(db, QualityMetricsCreate(**metrics_data_dict))
        return metrics
    except Exception as e:
        logger.error(f"Error creating quality metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating quality metrics: {str(e)}"
        )

@router.get("/quality-metrics", response_model=List[QualityMetricsResponse])
async def get_quality_metrics_endpoint(
    time_period: str,
    start_date: datetime,
    end_date: datetime,
    provider_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get quality metrics for a specific time period."""
    try:
        # Convert datetime fields to naive UTC
        start_date = ensure_naive_utc(start_date)
        end_date = ensure_naive_utc(end_date)
        
        # Call the service function with all required parameters
        metrics = await get_quality_metrics(
            db=db,
            provider_id=provider_id,
            time_period=time_period,
            start_date=start_date,
            end_date=end_date
        )
        return metrics
    except Exception as e:
        logger.error(f"Error getting quality metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting quality metrics: {str(e)}"
        )
