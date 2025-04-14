from sqlalchemy.orm import Session
from app.schemas.sustainability import SustainabilityRequest, SustainabilityResponse, SustainabilityInsight

async def process_sustainability_data(request: SustainabilityRequest, db: Session) -> SustainabilityResponse:
    """
    Processes sustainability data and provides recommendations for ethical health practices.
    """
    insights = []
    recommendation = "Keep making sustainable choices to improve health and environmental impact."
    
    # Analyze sustainable health practices
    if "recycling medical packaging" in request.health_practices:
        insights.append(SustainabilityInsight(insight="Recycling medical packaging helps reduce environmental waste."))
    
    if "using reusable medical supplies" in request.health_practices:
        insights.append(SustainabilityInsight(insight="Using reusable medical supplies reduces unnecessary waste."))
    
    # Encourage medication waste reduction
    if request.medication_waste_reduction:
        insights.append(SustainabilityInsight(insight="Reducing medication waste helps conserve resources and ensures proper disposal."))
    
    # Promote telehealth usage
    if request.telehealth_usage:
        insights.append(SustainabilityInsight(insight="Using telehealth reduces carbon footprint and increases healthcare accessibility."))
    
    if not insights:
        insights.append(SustainabilityInsight(insight="Consider adopting more sustainable health practices to contribute to a healthier environment."))
    
    return SustainabilityResponse(
        user_id=request.user_id,
        insights=insights,
        recommendation=recommendation
    )
