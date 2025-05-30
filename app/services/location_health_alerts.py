from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from app.db.models.health_checkin import HealthCheckIn
from app.db.models.family import FamilyHealthSummary
from app.core.config import settings
import httpx
import logging
from geopy.distance import geodesic

logger = logging.getLogger(__name__)

class LocationHealthAlertService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.weather_api_key = settings.WEATHER_API_KEY
        self.air_quality_api_key = settings.AIR_QUALITY_API_KEY

    async def get_location_health_alerts(
        self,
        latitude: float,
        longitude: float,
        radius_km: float = 10.0,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get comprehensive health alerts for a location."""
        try:
            alerts = {
                "environmental_alerts": await self._get_environmental_alerts(latitude, longitude),
                "disease_alerts": await self._get_disease_alerts(latitude, longitude, radius_km),
                "personal_health_alerts": await self._get_personal_health_alerts(user_id) if user_id else [],
                "facility_alerts": await self._get_facility_alerts(latitude, longitude, radius_km),
                "emergency_alerts": await self._get_emergency_alerts(latitude, longitude, radius_km)
            }
            
            return {
                "alerts": alerts,
                "risk_level": self._calculate_overall_risk_level(alerts),
                "recommendations": self._generate_recommendations(alerts),
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            logger.error(f"Error getting location health alerts: {str(e)}")
            raise

    async def _get_environmental_alerts(
        self,
        latitude: float,
        longitude: float
    ) -> List[Dict[str, Any]]:
        """Get environmental health alerts (air quality, weather, etc.)."""
        alerts = []
        
        # Get air quality data
        async with httpx.AsyncClient() as client:
            air_quality_url = f"http://api.openweathermap.org/data/2.5/air_pollution"
            params = {
                "lat": latitude,
                "lon": longitude,
                "appid": self.air_quality_api_key
            }
            response = await client.get(air_quality_url, params=params)
            air_data = response.json()
            
            if air_data.get("list"):
                aqi = air_data["list"][0]["main"]["aqi"]
                alerts.append({
                    "type": "air_quality",
                    "level": aqi,
                    "description": self._get_air_quality_description(aqi),
                    "timestamp": datetime.utcnow()
                })

        # Get weather alerts
        async with httpx.AsyncClient() as client:
            weather_url = f"http://api.openweathermap.org/data/2.5/weather"
            params = {
                "lat": latitude,
                "lon": longitude,
                "appid": self.weather_api_key
            }
            response = await client.get(weather_url, params=params)
            weather_data = response.json()
            
            if weather_data.get("weather"):
                alerts.append({
                    "type": "weather",
                    "condition": weather_data["weather"][0]["main"],
                    "description": weather_data["weather"][0]["description"],
                    "temperature": weather_data["main"]["temp"],
                    "timestamp": datetime.utcnow()
                })

        return alerts

    async def _get_disease_alerts(
        self,
        latitude: float,
        longitude: float,
        radius_km: float
    ) -> List[Dict[str, Any]]:
        """Get disease outbreak alerts for the area."""
        # This would typically integrate with a disease surveillance API
        # For now, returning mock data
        return [
            {
                "type": "disease_alert",
                "disease": "COVID-19",
                "risk_level": "moderate",
                "affected_area": f"{radius_km}km radius",
                "recommendations": ["Wear mask", "Maintain social distance"],
                "timestamp": datetime.utcnow()
            }
        ]

    async def _get_personal_health_alerts(
        self,
        user_id: int
    ) -> List[Dict[str, Any]]:
        """Get personalized health alerts based on user's health data."""
        alerts = []
        
        # Get user's recent health check-ins
        result = await self.db.execute(
            select(HealthCheckIn)
            .filter(HealthCheckIn.user_id == user_id)
            .order_by(HealthCheckIn.check_in_time.desc())
            .limit(5)
        )
        check_ins = result.scalars().all()
        
        # Get family health summary
        result = await self.db.execute(
            select(FamilyHealthSummary)
            .join(FamilyHealthSummary.family_link)
            .filter(FamilyHealthSummary.family_link.user_id == user_id)
            .order_by(FamilyHealthSummary.generated_at.desc())
            .limit(1)
        )
        family_summary = result.scalars().first()
        
        if check_ins:
            latest_checkin = check_ins[0]
            if latest_checkin.requires_attention:
                alerts.append({
                    "type": "health_checkin",
                    "severity": "high" if latest_checkin.risk_score > 0.7 else "moderate",
                    "reason": latest_checkin.attention_reason,
                    "timestamp": latest_checkin.check_in_time
                })
        
        if family_summary and family_summary.risk_factors:
            alerts.append({
                "type": "family_health",
                "risk_factors": family_summary.risk_factors,
                "timestamp": family_summary.generated_at
            })
        
        return alerts

    async def _get_facility_alerts(
        self,
        latitude: float,
        longitude: float,
        radius_km: float
    ) -> List[Dict[str, Any]]:
        """Get alerts about nearby health facilities."""
        # This would integrate with the existing health services locator
        # For now, returning mock data
        return [
            {
                "type": "facility_alert",
                "facility_type": "hospital",
                "status": "high_capacity",
                "wait_time": "45 minutes",
                "distance": "2.5 km",
                "timestamp": datetime.utcnow()
            }
        ]

    async def _get_emergency_alerts(
        self,
        latitude: float,
        longitude: float,
        radius_km: float
    ) -> List[Dict[str, Any]]:
        """Get emergency-related alerts for the area."""
        # This would integrate with the existing emergency service
        # For now, returning mock data
        return [
            {
                "type": "emergency_alert",
                "emergency_type": "traffic_accident",
                "location": "Main Street",
                "distance": "1.2 km",
                "timestamp": datetime.utcnow()
            }
        ]

    def _calculate_overall_risk_level(self, alerts: Dict[str, List[Dict[str, Any]]]) -> str:
        """Calculate overall risk level based on all alerts."""
        risk_scores = {
            "environmental_alerts": self._calculate_environmental_risk(alerts["environmental_alerts"]),
            "disease_alerts": self._calculate_disease_risk(alerts["disease_alerts"]),
            "personal_health_alerts": self._calculate_personal_health_risk(alerts["personal_health_alerts"]),
            "facility_alerts": self._calculate_facility_risk(alerts["facility_alerts"]),
            "emergency_alerts": self._calculate_emergency_risk(alerts["emergency_alerts"])
        }
        
        total_risk = sum(risk_scores.values()) / len(risk_scores)
        
        if total_risk >= 0.8:
            return "critical"
        elif total_risk >= 0.6:
            return "high"
        elif total_risk >= 0.4:
            return "moderate"
        elif total_risk >= 0.2:
            return "low"
        else:
            return "minimal"

    def _generate_recommendations(self, alerts: Dict[str, List[Dict[str, Any]]]) -> List[str]:
        """Generate recommendations based on alerts."""
        recommendations = []
        
        # Environmental recommendations
        for alert in alerts["environmental_alerts"]:
            if alert["type"] == "air_quality" and alert["level"] >= 4:
                recommendations.append("Consider staying indoors due to poor air quality")
            elif alert["type"] == "weather" and alert["condition"] in ["Thunderstorm", "Heavy Rain"]:
                recommendations.append("Take precautions for severe weather conditions")
        
        # Disease recommendations
        for alert in alerts["disease_alerts"]:
            if alert["risk_level"] in ["high", "moderate"]:
                recommendations.extend(alert["recommendations"])
        
        # Personal health recommendations
        for alert in alerts["personal_health_alerts"]:
            if alert["type"] == "health_checkin" and alert["severity"] == "high":
                recommendations.append("Schedule a medical check-up soon")
        
        # Facility recommendations
        for alert in alerts["facility_alerts"]:
            if alert["status"] == "high_capacity":
                recommendations.append(f"Consider alternative facilities due to high wait times at {alert['facility_type']}")
        
        return list(set(recommendations))  # Remove duplicates

    def _get_air_quality_description(self, aqi: int) -> str:
        """Get description for air quality index."""
        if aqi == 1:
            return "Good"
        elif aqi == 2:
            return "Fair"
        elif aqi == 3:
            return "Moderate"
        elif aqi == 4:
            return "Poor"
        else:
            return "Very Poor"

    def _calculate_environmental_risk(self, alerts: List[Dict[str, Any]]) -> float:
        """Calculate risk score for environmental alerts."""
        if not alerts:
            return 0.0
        
        risk_score = 0.0
        for alert in alerts:
            if alert["type"] == "air_quality":
                risk_score += alert["level"] / 5.0
            elif alert["type"] == "weather":
                if alert["condition"] in ["Thunderstorm", "Heavy Rain", "Snow"]:
                    risk_score += 0.8
        
        return min(risk_score / len(alerts), 1.0)

    def _calculate_disease_risk(self, alerts: List[Dict[str, Any]]) -> float:
        """Calculate risk score for disease alerts."""
        if not alerts:
            return 0.0
        
        risk_levels = {"low": 0.2, "moderate": 0.5, "high": 0.8, "critical": 1.0}
        return sum(risk_levels.get(alert["risk_level"], 0.0) for alert in alerts) / len(alerts)

    def _calculate_personal_health_risk(self, alerts: List[Dict[str, Any]]) -> float:
        """Calculate risk score for personal health alerts."""
        if not alerts:
            return 0.0
        
        risk_score = 0.0
        for alert in alerts:
            if alert["type"] == "health_checkin":
                risk_score += 0.8 if alert["severity"] == "high" else 0.4
            elif alert["type"] == "family_health":
                risk_score += 0.6
        
        return min(risk_score / len(alerts), 1.0)

    def _calculate_facility_risk(self, alerts: List[Dict[str, Any]]) -> float:
        """Calculate risk score for facility alerts."""
        if not alerts:
            return 0.0
        
        risk_score = 0.0
        for alert in alerts:
            if alert["status"] == "high_capacity":
                risk_score += 0.7
            elif alert["status"] == "closed":
                risk_score += 0.9
        
        return min(risk_score / len(alerts), 1.0)

    def _calculate_emergency_risk(self, alerts: List[Dict[str, Any]]) -> float:
        """Calculate risk score for emergency alerts."""
        if not alerts:
            return 0.0
        
        return min(len(alerts) * 0.3, 1.0)  # Each emergency alert contributes 0.3 to the risk score 