from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.monitoring import ChronicMonitoringRequest, ChronicMonitoringResponse
from app.services.monitoring_service import process_chronic_monitoring
from app.api.endpoints.dependencies import get_db, get_current_user
from sqlalchemy.future import select
from app.db.models.monitoring import ChronicMonitoring
from app.db.models.caregiver import CaregiverAssignment
from app.db.models.user import User, UserRoleInput
from app.services.automated_health_monitor import AutomatedHealthMonitor
from typing import List, Dict, Any
import logging
from datetime import datetime

router = APIRouter()
logger = logging.getLogger(__name__)

# Chronic Disease Monitoring Endpoints
@router.post("/chronic", response_model=ChronicMonitoringResponse)
async def chronic_disease_monitoring(
    request: ChronicMonitoringRequest,
    db: Session = Depends(get_db),
    db_user = Depends(get_current_user)
):
    """
    Processes and analyzes data for chronic disease monitoring, such as diabetes, hypertension, and cardiovascular health.
    """
    try:
        monitoring_data = await process_chronic_monitoring(request, db)
        return monitoring_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chronic/{patient_id}")
async def get_chronic_monitoring(
    patient_id: int, 
    db: AsyncSession = Depends(get_db), 
    db_user = Depends(get_current_user)
):
    """
    Retrieve chronic disease monitoring records for a given patient.
    """
    result = await db.execute(select(ChronicMonitoring).where(ChronicMonitoring.patient_id == patient_id))
    records = result.scalars().all()
    if not records:
        raise HTTPException(status_code=404, detail="No chronic monitoring records found for this patient.")
    return records

# Automated Health Monitoring Endpoints
@router.get("/analysis/{user_id}", response_model=Dict[str, Any])
async def get_health_analysis(
    user_id: int,
    days: int = 30,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive health analysis for a user.
    """
    if current_user.id != user_id and current_user.role not in [UserRoleInput.PRACTITIONER, UserRoleInput.ADMIN]:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to view this user's health analysis"
        )

    try:
        monitor = AutomatedHealthMonitor(db)
        analysis = await monitor.analyze_health_patterns(user_id, days)
        return analysis
    except Exception as e:
        logger.error(f"Failed to get health analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/check-status/{user_id}")
async def check_health_status(
    user_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Check current health status and generate alerts if needed.
    """
    if current_user.id != user_id and current_user.role not in [UserRoleInput.PRACTITIONER, UserRoleInput.ADMIN]:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to check this user's health status"
        )

    try:
        monitor = AutomatedHealthMonitor(db)
        risk_score, alerts = await monitor.check_health_status(user_id)
        
        return {
            "user_id": user_id,
            "risk_score": risk_score,
            "alerts": alerts,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Failed to check health status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/risk-factors/{user_id}", response_model=List[Dict[str, Any]])
async def get_risk_factors(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get identified risk factors for a user.
    """
    if current_user.id != user_id and current_user.role not in [UserRoleInput.PRACTITIONER, UserRoleInput.ADMIN]:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to view this user's risk factors"
        )

    try:
        monitor = AutomatedHealthMonitor(db)
        history = await monitor._get_health_history(user_id, days=30)
        risk_factors = await monitor._calculate_risk_factors(history)
        return risk_factors
    except Exception as e:
        logger.error(f"Failed to get risk factors: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/recommendations/{user_id}", response_model=List[str])
async def get_health_recommendations(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get personalized health recommendations for a user.
    """
    if current_user.id != user_id and current_user.role not in [UserRoleInput.PRACTITIONER, UserRoleInput.ADMIN]:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to view this user's recommendations"
        )

    try:
        monitor = AutomatedHealthMonitor(db)
        history = await monitor._get_health_history(user_id, days=30)
        
        # Get analysis components
        metrics_matrix = monitor._prepare_metrics_matrix(history)
        anomalies = monitor._detect_anomalies(metrics_matrix)
        trends = monitor.predictive_analytics.analyze_health_trends(history)
        risk_factors = await monitor._calculate_risk_factors(history)
        
        # Generate recommendations
        recommendations = monitor._generate_recommendations(anomalies, trends, risk_factors)
        return recommendations
    except Exception as e:
        logger.error(f"Failed to get health recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
