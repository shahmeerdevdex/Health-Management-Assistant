from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
import logging
from typing import Optional, List, Dict, Any
from app.db.models.health_checkin import HealthCheckIn
from app.db.models.monitoring import ChronicMonitoring
from app.db.models.health_diary import HealthDiary
from app.db.models.user import User
from app.schemas.monitoring import VitalSigns, PatientStatus, RiskAssessment

logger = logging.getLogger(__name__)

class AutomatedHealthMonitor:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.alert_thresholds = {
            "heart_rate": {"min": 60, "max": 100},
            "blood_pressure_systolic": {"min": 90, "max": 140},
            "blood_pressure_diastolic": {"min": 60, "max": 90},
            "blood_sugar": {"min": 70, "max": 180},
            "temperature": {"min": 36.1, "max": 37.2}
        }

    async def check_vitals(self, user_id: int) -> Dict[str, Any]:
        """Check user's vital signs against normal ranges."""
        try:
            # Get latest health metrics from check-ins
            latest_checkin = await self._get_latest_checkin(user_id)
            if not latest_checkin:
                return {"status": "no_data", "message": "No health metrics available"}

            alerts = []
            metrics = latest_checkin.health_metrics

            for metric, value in metrics.items():
                if metric in self.alert_thresholds:
                    thresholds = self.alert_thresholds[metric]
                    if value < thresholds["min"]:
                        alerts.append(f"{metric} is below normal range")
                    elif value > thresholds["max"]:
                        alerts.append(f"{metric} is above normal range")

            return {
                "status": "warning" if alerts else "normal",
                "alerts": alerts,
                "metrics": metrics,
                "check_in_time": latest_checkin.check_in_time
            }
        except Exception as e:
            logger.error(f"Error checking vitals: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def _get_latest_checkin(self, user_id: int) -> Optional[HealthCheckIn]:
        """Get the latest health check-in for a user."""
        try:
            # This would typically query the database for the latest check-in
            # For now, return dummy data
            return HealthCheckIn(
                user_id=user_id,
                check_in_time=datetime.utcnow(),
                health_metrics={
                    "heart_rate": 75,
                    "blood_pressure_systolic": 120,
                    "blood_pressure_diastolic": 80,
                    "blood_sugar": 100,
                    "temperature": 36.6
                },
                risk_score=0.1,
                requires_attention=False
            )
        except Exception as e:
            logger.error(f"Error getting latest check-in: {str(e)}")
            return None

    async def monitor_health_trends(self, user_id: int, days: int = 7) -> Dict[str, Any]:
        """Monitor health trends over a specified period."""
        try:
            # Get chronic monitoring data
            chronic_data = await self._get_chronic_monitoring(user_id)
            # Get health diary entries
            diary_entries = await self._get_health_diary_entries(user_id, days)
            
            return {
                "status": "stable",
                "chronic_conditions": chronic_data,
                "recent_entries": diary_entries,
                "analysis": {
                    "mood_trend": self._analyze_mood_trend(diary_entries),
                    "symptom_frequency": self._analyze_symptoms(diary_entries)
                }
            }
        except Exception as e:
            logger.error(f"Error monitoring health trends: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def _get_chronic_monitoring(self, user_id: int) -> Optional[ChronicMonitoring]:
        """Get chronic monitoring data for a user."""
        try:
            # This would typically query the database
            # For now, return dummy data
            return ChronicMonitoring(
                patient_id=user_id,
                condition="diabetes",
                blood_pressure=[{"systolic": 120, "diastolic": 80, "timestamp": datetime.utcnow()}],
                blood_sugar=[{"value": 100, "timestamp": datetime.utcnow()}],
                heart_rate=[{"value": 75, "timestamp": datetime.utcnow()}],
                weight=[{"value": 70, "timestamp": datetime.utcnow()}]
            )
        except Exception as e:
            logger.error(f"Error getting chronic monitoring data: {str(e)}")
            return None

    async def _get_health_diary_entries(self, user_id: int, days: int) -> List[HealthDiary]:
        """Get health diary entries for a user over a specified period."""
        try:
            # This would typically query the database
            # For now, return dummy data
            return [
                HealthDiary(
                    user_id=user_id,
                    date=datetime.utcnow() - timedelta(days=i),
                    symptoms=["headache", "fatigue"],
                    mood=7,
                    notes="Feeling better today"
                ) for i in range(days)
            ]
        except Exception as e:
            logger.error(f"Error getting health diary entries: {str(e)}")
            return []

    def _analyze_mood_trend(self, entries: List[HealthDiary]) -> Dict[str, Any]:
        """Analyze mood trends from health diary entries."""
        if not entries:
            return {"status": "no_data"}
        
        moods = [entry.mood for entry in entries if entry.mood is not None]
        if not moods:
            return {"status": "no_data"}
            
        return {
            "average": sum(moods) / len(moods),
            "trend": "improving" if moods[-1] > moods[0] else "declining" if moods[-1] < moods[0] else "stable",
            "range": {"min": min(moods), "max": max(moods)}
        }

    def _analyze_symptoms(self, entries: List[HealthDiary]) -> Dict[str, int]:
        """Analyze symptom frequency from health diary entries."""
        symptom_count = {}
        for entry in entries:
            if entry.symptoms:
                for symptom in entry.symptoms:
                    symptom_count[symptom] = symptom_count.get(symptom, 0) + 1
        return symptom_count

    async def generate_health_report(self, user_id: int) -> Dict[str, Any]:
        """Generate a comprehensive health report."""
        try:
            vitals = await self.check_vitals(user_id)
            trends = await self.monitor_health_trends(user_id)
            
            return {
                "timestamp": datetime.utcnow(),
                "vitals_status": vitals,
                "trends_analysis": trends,
                "recommendations": self._generate_recommendations(vitals, trends)
            }
        except Exception as e:
            logger.error(f"Error generating health report: {str(e)}")
            return {"status": "error", "message": str(e)}

    def _generate_recommendations(self, vitals: Dict[str, Any], trends: Dict[str, Any]) -> List[str]:
        """Generate health recommendations based on vitals and trends."""
        recommendations = []
        
        if vitals.get("status") == "warning":
            for alert in vitals.get("alerts", []):
                if "heart_rate" in alert:
                    recommendations.append("Consider taking a short rest and monitoring your heart rate")
                elif "blood_pressure" in alert:
                    recommendations.append("Consider consulting your healthcare provider about your blood pressure")
                elif "blood_sugar" in alert:
                    recommendations.append("Monitor your blood sugar levels and adjust your diet if necessary")
                elif "temperature" in alert:
                    recommendations.append("Monitor your temperature and consider consulting a doctor if it persists")

        # Add recommendations based on mood trends
        mood_analysis = trends.get("analysis", {}).get("mood_trend", {})
        if mood_analysis.get("trend") == "declining":
            recommendations.append("Consider reaching out to your support network or healthcare provider about your mood")

        # Add recommendations based on symptom frequency
        symptoms = trends.get("analysis", {}).get("symptom_frequency", {})
        for symptom, frequency in symptoms.items():
            if frequency > 3:  # If symptom appears more than 3 times
                recommendations.append(f"Consider discussing your frequent {symptom} with your healthcare provider")

        return recommendations

# Create a singleton instance
health_monitor = AutomatedHealthMonitor(None)  # DB session will be set when used 