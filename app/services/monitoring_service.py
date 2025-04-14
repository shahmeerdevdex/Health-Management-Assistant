from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from app.schemas.monitoring import ChronicMonitoringRequest, ChronicMonitoringResponse
from app.db.models.monitoring import ChronicMonitoring
from datetime import datetime
from app.services.ai_services import analyze_chronic_health_data

async def process_chronic_monitoring(request: ChronicMonitoringRequest, db: AsyncSession) -> ChronicMonitoringResponse:
    """
    Stores and processes chronic disease data using AI-generated insights.
    """

    # Extract validated data from Pydantic model
    patient_id = request.patient_id
    blood_pressure = request.blood_pressure or []
    blood_sugar = request.blood_sugar or []
    heart_rate = request.heart_rate or []
    weight = request.weight or []
    medications = request.medications or []

    # Call AI service to analyze the chronic health data
    insights = await analyze_chronic_health_data(
        condition=request.condition,
        blood_pressure=[bp.dict() for bp in blood_pressure],
        blood_sugar=blood_sugar,
        heart_rate=heart_rate,
        weight=weight,
        medications=medications
    )

    summary = "Chronic disease monitoring analysis completed. " + ("Insights generated." if insights else "No major concerns detected.")

    # Store the data in the database
    try:
        monitoring_record = ChronicMonitoring(
            patient_id=patient_id,
            condition=request.condition,
            blood_pressure=[bp.dict() for bp in blood_pressure],
            blood_sugar=blood_sugar,
            heart_rate=heart_rate,
            weight=weight,
            medications=medications,
            recorded_at=datetime.utcnow()
        )
        db.add(monitoring_record)
        await db.commit()
        await db.refresh(monitoring_record)
    except SQLAlchemyError as e:
        await db.rollback()
        raise Exception(f"Database error: {str(e)}")

    return ChronicMonitoringResponse(
        summary=summary,
        insights=insights
    )
