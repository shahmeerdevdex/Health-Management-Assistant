from datetime import datetime, timedelta
from typing import List, Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from app.db.models.provider_analytics import (
    ProviderAnalytics,
    PopulationHealthMetrics,
    QualityMetrics,
    OperationalMetrics,
    ReportType
)
from app.schemas.provider_analytics import (
    ProviderAnalyticsCreate,
    PopulationHealthMetricsCreate,
    QualityMetricsCreate,
    OperationalMetricsCreate,
    AnalyticsRequest
)

import logging

logger = logging.getLogger(__name__)

async def create_provider_analytics(
    db: AsyncSession,
    analytics_data: ProviderAnalyticsCreate
) -> ProviderAnalytics:
    """Create a new provider analytics record."""
    analytics = ProviderAnalytics(**analytics_data.dict())
    db.add(analytics)
    await db.commit()
    await db.refresh(analytics)
    return analytics

async def get_provider_analytics(
    db: AsyncSession,
    provider_id: int,
    report_type: ReportType,
    time_period: str,
    start_date: datetime,
    end_date: datetime
) -> List[ProviderAnalytics]:
    """Get provider analytics for a specific time period."""
    query = select(ProviderAnalytics).where(
        and_(
            ProviderAnalytics.provider_id == provider_id,
            ProviderAnalytics.report_type == report_type,
            ProviderAnalytics.time_period == time_period,
            ProviderAnalytics.start_date >= start_date,
            ProviderAnalytics.end_date <= end_date
        )
    )
    result = await db.execute(query)
    return result.scalars().all()

async def create_population_health_metrics(
    db: AsyncSession,
    metrics_data: PopulationHealthMetricsCreate
) -> PopulationHealthMetrics:
    """Create new population health metrics."""
    metrics = PopulationHealthMetrics(**metrics_data.dict())
    db.add(metrics)
    await db.commit()
    await db.refresh(metrics)
    return metrics

async def get_population_health_metrics(
    db: AsyncSession,
    provider_id: int,
    time_period: str,
    start_date: datetime,
    end_date: datetime
) -> List[PopulationHealthMetrics]:
    """Get population health metrics for a specific time period."""
    query = select(PopulationHealthMetrics).where(
        and_(
            PopulationHealthMetrics.provider_id == provider_id,
            PopulationHealthMetrics.time_period == time_period,
            PopulationHealthMetrics.start_date >= start_date,
            PopulationHealthMetrics.end_date <= end_date
        )
    )
    result = await db.execute(query)
    return result.scalars().all()

async def create_quality_metrics(
    db: AsyncSession,
    metrics_data: QualityMetricsCreate
) -> QualityMetrics:
    """Create new quality metrics."""
    metrics = QualityMetrics(**metrics_data.dict())
    db.add(metrics)
    await db.commit()
    await db.refresh(metrics)
    return metrics

async def get_quality_metrics(
    db: AsyncSession,
    provider_id: int,
    time_period: str,
    start_date: datetime,
    end_date: datetime
) -> List[QualityMetrics]:
    """Get quality metrics for a specific time period."""
    query = select(QualityMetrics).where(
        and_(
            QualityMetrics.provider_id == provider_id,
            QualityMetrics.time_period == time_period,
            QualityMetrics.start_date >= start_date,
            QualityMetrics.end_date <= end_date
        )
    )
    result = await db.execute(query)
    return result.scalars().all()

async def create_operational_metrics(
    db: AsyncSession,
    metrics_data: OperationalMetricsCreate
) -> OperationalMetrics:
    """Create new operational metrics."""
    metrics = OperationalMetrics(**metrics_data.dict())
    db.add(metrics)
    await db.commit()
    await db.refresh(metrics)
    return metrics

async def get_operational_metrics(
    db: AsyncSession,
    provider_id: int,
    time_period: str,
    start_date: datetime,
    end_date: datetime
) -> List[OperationalMetrics]:
    """Get operational metrics for a specific time period."""
    query = select(OperationalMetrics).where(
        and_(
            OperationalMetrics.provider_id == provider_id,
            OperationalMetrics.time_period == time_period,
            OperationalMetrics.start_date >= start_date,
            OperationalMetrics.end_date <= end_date
        )
    )
    result = await db.execute(query)
    return result.scalars().all()

async def generate_analytics_report(
    db: AsyncSession,
    request: AnalyticsRequest
) -> Dict:
    """Generate a comprehensive analytics report."""
    try:
        # Get all relevant metrics based on report type
        if request.report_type == ReportType.POPULATION_HEALTH:
            metrics = await get_population_health_metrics(
                db, request.provider_id, request.time_period,
                request.start_date, request.end_date
            )
        elif request.report_type == ReportType.QUALITY_METRICS:
            metrics = await get_quality_metrics(
                db, request.provider_id, request.time_period,
                request.start_date, request.end_date
            )
        elif request.report_type == ReportType.OPERATIONAL:
            metrics = await get_operational_metrics(
                db, request.provider_id, request.time_period,
                request.start_date, request.end_date
            )
        else:
            metrics = await get_provider_analytics(
                db, request.provider_id, request.report_type,
                request.time_period, request.start_date, request.end_date
            )

        # Process metrics and generate insights
        processed_metrics = {}
        trends = []
        recommendations = []

        for metric in metrics:
            metric_name = getattr(metric, 'metric_name', None) or 'metrics'
            value = getattr(metric, 'value', None) or metric.metrics
            
            processed_metrics[metric_name] = value
            
            # Analyze trends
            if hasattr(metric, 'value'):
                trend = {
                    'metric': metric_name,
                    'value': value,
                    'target': getattr(metric, 'target_value', None) or getattr(metric, 'benchmark', None),
                    'unit': getattr(metric, 'unit', None)
                }
                trends.append(trend)

        # Generate recommendations based on metrics
        if request.report_type == ReportType.POPULATION_HEALTH:
            recommendations = await generate_population_health_recommendations(processed_metrics)
        elif request.report_type == ReportType.QUALITY_METRICS:
            recommendations = await generate_quality_metrics_recommendations(processed_metrics)
        elif request.report_type == ReportType.OPERATIONAL:
            recommendations = await generate_operational_recommendations(processed_metrics)

        return {
            'provider_id': request.provider_id,
            'report_type': request.report_type,
            'time_period': request.time_period,
            'start_date': request.start_date,
            'end_date': request.end_date,
            'metrics': processed_metrics,
            'summary': generate_summary(processed_metrics),
            'trends': trends,
            'recommendations': recommendations
        }
    except Exception as e:
        logger.error(f"Error generating analytics report: {str(e)}")
        raise

async def generate_population_health_recommendations(metrics: Dict) -> List[str]:
    """Generate recommendations based on population health metrics."""
    recommendations = []
    
    if 'diabetes_prevalence' in metrics and metrics['diabetes_prevalence'] > 10:
        recommendations.append("Consider implementing a diabetes prevention program")
    
    if 'vaccination_rate' in metrics and metrics['vaccination_rate'] < 80:
        recommendations.append("Develop a vaccination awareness campaign")
    
    if 'obesity_rate' in metrics and metrics['obesity_rate'] > 30:
        recommendations.append("Implement nutrition and physical activity programs")
    
    return recommendations

async def generate_quality_metrics_recommendations(metrics: Dict) -> List[str]:
    """Generate recommendations based on quality metrics."""
    recommendations = []
    
    if 'readmission_rate' in metrics and metrics['readmission_rate'] > 15:
        recommendations.append("Review discharge planning and follow-up care processes")
    
    if 'patient_satisfaction' in metrics and metrics['patient_satisfaction'] < 4:
        recommendations.append("Conduct patient satisfaction surveys and implement improvements")
    
    if 'medication_adherence' in metrics and metrics['medication_adherence'] < 80:
        recommendations.append("Implement medication adherence support programs")
    
    return recommendations

async def generate_operational_recommendations(metrics: Dict) -> List[str]:
    """Generate recommendations based on operational metrics."""
    recommendations = []
    
    if 'appointment_utilization' in metrics and metrics['appointment_utilization'] < 85:
        recommendations.append("Optimize appointment scheduling and reduce no-shows")
    
    if 'wait_time' in metrics and metrics['wait_time'] > 30:
        recommendations.append("Implement wait time reduction strategies")
    
    if 'resource_utilization' in metrics and metrics['resource_utilization'] < 70:
        recommendations.append("Review resource allocation and staffing patterns")
    
    return recommendations

def generate_summary(metrics: Dict) -> Dict:
    """Generate a summary of the metrics."""
    summary = {
        'total_metrics': len(metrics),
        'key_findings': [],
        'areas_of_concern': [],
        'areas_of_excellence': []
    }
    
    for metric_name, value in metrics.items():
        if isinstance(value, (int, float)):
            if value < 50:  # Example threshold
                summary['areas_of_concern'].append(metric_name)
            elif value > 90:  # Example threshold
                summary['areas_of_excellence'].append(metric_name)
            summary['key_findings'].append(f"{metric_name}: {value}")
    
    return summary 