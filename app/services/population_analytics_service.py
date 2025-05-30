from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc
from app.db.models.provider_analytics import (
    ProviderAnalytics,
    PopulationHealthMetrics,
    ReportType
)
from app.schemas.provider_analytics import AnalyticsRequest
import logging

logger = logging.getLogger(__name__)

async def get_aggregated_population_metrics(
    db: AsyncSession,
    hospital_id: int,
    time_period: str,
    start_date: datetime,
    end_date: datetime
) -> Dict:
    """Get aggregated population health metrics across all providers in a hospital."""
    try:
        # Aggregate metrics across all providers
        query = select(
            func.avg(PopulationHealthMetrics.value).label('average_value'),
            func.min(PopulationHealthMetrics.value).label('min_value'),
            func.max(PopulationHealthMetrics.value).label('max_value'),
            PopulationHealthMetrics.metric_name,
            PopulationHealthMetrics.unit
        ).where(
            and_(
                PopulationHealthMetrics.provider_id.in_(
                    select(User.id).where(User.hospital_id == hospital_id)
                ),
                PopulationHealthMetrics.time_period == time_period,
                PopulationHealthMetrics.start_date >= start_date,
                PopulationHealthMetrics.end_date <= end_date
            )
        ).group_by(
            PopulationHealthMetrics.metric_name,
            PopulationHealthMetrics.unit
        )
        
        result = await db.execute(query)
        metrics = result.all()
        
        return {
            metric.metric_name: {
                'average': metric.average_value,
                'min': metric.min_value,
                'max': metric.max_value,
                'unit': metric.unit
            }
            for metric in metrics
        }
    except Exception as e:
        logger.error(f"Error getting aggregated population metrics: {str(e)}")
        raise

async def get_comparative_analytics(
    db: AsyncSession,
    provider_ids: List[int],
    time_period: str,
    start_date: datetime,
    end_date: datetime
) -> Dict:
    """Get comparative analytics between different providers."""
    try:
        comparative_data = {}
        
        for provider_id in provider_ids:
            metrics = await get_provider_analytics(
                db, provider_id, ReportType.POPULATION_HEALTH,
                time_period, start_date, end_date
            )
            
            comparative_data[provider_id] = {
                'metrics': metrics,
                'performance_score': calculate_performance_score(metrics),
                'trends': analyze_metrics_trends(metrics)
            }
        
        return comparative_data
    except Exception as e:
        logger.error(f"Error getting comparative analytics: {str(e)}")
        raise

async def get_real_time_population_health(
    db: AsyncSession,
    hospital_id: int,
    metric_names: Optional[List[str]] = None
) -> Dict:
    """Get real-time population health monitoring data."""
    try:
        current_time = datetime.utcnow()
        time_window = current_time - timedelta(hours=24)
        
        query = select(PopulationHealthMetrics).where(
            and_(
                PopulationHealthMetrics.provider_id.in_(
                    select(User.id).where(User.hospital_id == hospital_id)
                ),
                PopulationHealthMetrics.start_date >= time_window,
                PopulationHealthMetrics.metric_name.in_(metric_names) if metric_names else True
            )
        ).order_by(desc(PopulationHealthMetrics.start_date))
        
        result = await db.execute(query)
        metrics = result.scalars().all()
        
        return process_real_time_metrics(metrics)
    except Exception as e:
        logger.error(f"Error getting real-time population health: {str(e)}")
        raise

def calculate_performance_score(metrics: List[Dict]) -> float:
    """Calculate a performance score based on metrics."""
    if not metrics:
        return 0.0
    
    total_score = 0
    weight_sum = 0
    
    for metric in metrics:
        weight = get_metric_weight(metric['metric_name'])
        score = calculate_metric_score(metric)
        total_score += score * weight
        weight_sum += weight
    
    return total_score / weight_sum if weight_sum > 0 else 0.0

def analyze_metrics_trends(metrics: List[Dict]) -> List[Dict]:
    """Analyze trends in metrics over time."""
    trends = []
    
    for metric in metrics:
        trend = {
            'metric_name': metric['metric_name'],
            'direction': determine_trend_direction(metric),
            'magnitude': calculate_trend_magnitude(metric),
            'significance': assess_trend_significance(metric)
        }
        trends.append(trend)
    
    return trends

def process_real_time_metrics(metrics: List[Dict]) -> Dict:
    """Process real-time metrics for monitoring."""
    processed_data = {
        'current_values': {},
        'alerts': [],
        'trends': {}
    }
    
    for metric in metrics:
        metric_name = metric['metric_name']
        value = metric['value']
        
        # Update current values
        processed_data['current_values'][metric_name] = value
        
        # Check for alerts
        if is_alert_threshold_breached(metric):
            processed_data['alerts'].append({
                'metric': metric_name,
                'value': value,
                'threshold': get_alert_threshold(metric_name),
                'timestamp': metric['start_date']
            })
        
        # Update trends
        if metric_name not in processed_data['trends']:
            processed_data['trends'][metric_name] = []
        processed_data['trends'][metric_name].append({
            'value': value,
            'timestamp': metric['start_date']
        })
    
    return processed_data

def get_metric_weight(metric_name: str) -> float:
    """Get the weight for a specific metric."""
    weights = {
        'diabetes_prevalence': 1.5,
        'vaccination_rate': 1.2,
        'obesity_rate': 1.0,
        'blood_pressure_control': 1.3,
        'smoking_rate': 1.1
    }
    return weights.get(metric_name, 1.0)

def calculate_metric_score(metric: Dict) -> float:
    """Calculate a score for a specific metric."""
    value = metric['value']
    target = metric.get('target_value')
    
    if target is None:
        return 0.0
    
    # Normalize the score between 0 and 1
    return max(0, min(1, value / target))

def determine_trend_direction(metric: Dict) -> str:
    """Determine the direction of a metric trend."""
    # Implementation would compare current value with historical values
    return "increasing"  # Placeholder

def calculate_trend_magnitude(metric: Dict) -> float:
    """Calculate the magnitude of a trend."""
    # Implementation would calculate the rate of change
    return 0.0  # Placeholder

def assess_trend_significance(metric: Dict) -> str:
    """Assess the significance of a trend."""
    # Implementation would use statistical methods
    return "significant"  # Placeholder

def is_alert_threshold_breached(metric: Dict) -> bool:
    """Check if a metric has breached its alert threshold."""
    threshold = get_alert_threshold(metric['metric_name'])
    return metric['value'] > threshold

def get_alert_threshold(metric_name: str) -> float:
    """Get the alert threshold for a specific metric."""
    thresholds = {
        'diabetes_prevalence': 15.0,
        'vaccination_rate': 70.0,
        'obesity_rate': 35.0,
        'blood_pressure_control': 80.0,
        'smoking_rate': 20.0
    }
    return thresholds.get(metric_name, 0.0)

async def generate_comprehensive_report(
    db: AsyncSession,
    hospital_id: int,
    time_period: str,
    start_date: datetime,
    end_date: datetime,
    report_type: str = "full"
) -> Dict:
    """Generate a comprehensive report combining all analytics data."""
    try:
        # Get aggregated metrics
        aggregated_metrics = await get_aggregated_population_metrics(
            db, hospital_id, time_period, start_date, end_date
        )
        
        # Get real-time metrics
        real_time_metrics = await get_real_time_population_health(
            db, hospital_id
        )
        
        # Get all providers in the hospital
        providers_query = select(User.id).where(User.hospital_id == hospital_id)
        result = await db.execute(providers_query)
        provider_ids = [row[0] for row in result.all()]
        
        # Get comparative analytics
        comparative_data = await get_comparative_analytics(
            db, provider_ids, time_period, start_date, end_date
        )
        
        # Generate report sections based on type
        report_sections = {
            "summary": generate_summary_section(aggregated_metrics, real_time_metrics),
            "trends": generate_trends_section(aggregated_metrics, real_time_metrics),
            "comparative": generate_comparative_section(comparative_data),
            "alerts": generate_alerts_section(real_time_metrics),
            "recommendations": generate_recommendations_section(
                aggregated_metrics, real_time_metrics, comparative_data
            )
        }
        
        # Filter sections based on report type
        if report_type == "summary":
            return {"summary": report_sections["summary"]}
        elif report_type == "trends":
            return {
                "summary": report_sections["summary"],
                "trends": report_sections["trends"]
            }
        elif report_type == "alerts":
            return {
                "summary": report_sections["summary"],
                "alerts": report_sections["alerts"]
            }
        
        return report_sections
    except Exception as e:
        logger.error(f"Error generating comprehensive report: {str(e)}")
        raise

def generate_summary_section(aggregated_metrics: Dict, real_time_metrics: Dict) -> Dict:
    """Generate summary section of the report."""
    return {
        "overview": {
            "total_metrics": len(aggregated_metrics),
            "active_alerts": len(real_time_metrics.get("alerts", [])),
            "metrics_status": {
                metric: {
                    "current": real_time_metrics["current_values"].get(metric),
                    "average": data["average"],
                    "status": "critical" if is_alert_threshold_breached({
                        "metric_name": metric,
                        "value": real_time_metrics["current_values"].get(metric, 0)
                    }) else "normal"
                }
                for metric, data in aggregated_metrics.items()
            }
        }
    }

def generate_trends_section(aggregated_metrics: Dict, real_time_metrics: Dict) -> Dict:
    """Generate trends section of the report."""
    return {
        "metric_trends": {
            metric: {
                "historical": aggregated_metrics[metric],
                "recent": real_time_metrics["trends"].get(metric, []),
                "direction": determine_trend_direction({
                    "metric_name": metric,
                    "value": real_time_metrics["current_values"].get(metric, 0)
                })
            }
            for metric in aggregated_metrics.keys()
        }
    }

def generate_comparative_section(comparative_data: Dict) -> Dict:
    """Generate comparative section of the report."""
    return {
        "provider_comparison": {
            provider_id: {
                "performance_score": data["performance_score"],
                "key_metrics": {
                    metric["metric_name"]: metric["value"]
                    for metric in data["metrics"]
                },
                "trends": data["trends"]
            }
            for provider_id, data in comparative_data.items()
        }
    }

def generate_alerts_section(real_time_metrics: Dict) -> Dict:
    """Generate alerts section of the report."""
    return {
        "active_alerts": real_time_metrics.get("alerts", []),
        "alert_summary": {
            "total_alerts": len(real_time_metrics.get("alerts", [])),
            "critical_alerts": len([
                alert for alert in real_time_metrics.get("alerts", [])
                if alert["value"] > get_alert_threshold(alert["metric"]) * 1.5
            ])
        }
    }

def generate_recommendations_section(
    aggregated_metrics: Dict,
    real_time_metrics: Dict,
    comparative_data: Dict
) -> Dict:
    """Generate recommendations section of the report."""
    recommendations = []
    
    # Analyze metrics and generate recommendations
    for metric, data in aggregated_metrics.items():
        current_value = real_time_metrics["current_values"].get(metric, 0)
        
        if current_value > data["average"] * 1.2:
            recommendations.append({
                "metric": metric,
                "type": "improvement",
                "message": f"Consider implementing interventions to reduce {metric}",
                "priority": "high" if current_value > get_alert_threshold(metric) else "medium"
            })
        elif current_value < data["average"] * 0.8:
            recommendations.append({
                "metric": metric,
                "type": "maintenance",
                "message": f"Maintain current practices for {metric}",
                "priority": "low"
            })
    
    # Add comparative recommendations
    for provider_id, data in comparative_data.items():
        if data["performance_score"] < 0.6:
            recommendations.append({
                "type": "provider_support",
                "message": f"Consider additional support for provider {provider_id}",
                "priority": "high"
            })
    
    return {
        "recommendations": recommendations,
        "priority_summary": {
            "high": len([r for r in recommendations if r["priority"] == "high"]),
            "medium": len([r for r in recommendations if r["priority"] == "medium"]),
            "low": len([r for r in recommendations if r["priority"] == "low"])
        }
    } 