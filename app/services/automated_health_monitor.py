from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from app.db.models.health_checkin import HealthCheckIn
from app.schemas.health_checkin import HealthMetrics
from app.services.notification_service import send_notification
from app.services.ai_services import PredictiveHealthAnalytics
from app.services.care_plan_service import get_user_care_plans
import numpy as np
from sklearn.ensemble import IsolationForest, RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import logging
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.db.models.care_plan import CarePlan
from app.db.models.user import User

logger = logging.getLogger(__name__)

class AutomatedHealthMonitor:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.predictive_analytics = PredictiveHealthAnalytics()
        self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
        self.scaler = StandardScaler()
        self.scheduler = AsyncIOScheduler()
        self.predictive_model = RandomForestRegressor(n_estimators=100, random_state=42)
        self._initialize_scheduler()

    def _initialize_scheduler(self):
        """Initialize the scheduler for automated health check-ins."""
        self.scheduler.start()
        # Schedule daily health check-ins
        self.scheduler.add_job(
            self.run_scheduled_checkins,
            CronTrigger(hour=9, minute=0),  # 9 AM daily
            id='daily_health_check'
        )
        # Schedule weekly predictive analysis
        self.scheduler.add_job(
            self.run_predictive_analysis,
            CronTrigger(day_of_week='mon', hour=0, minute=0),  # Every Monday at midnight
            id='weekly_predictive_analysis'
        )

    async def run_scheduled_checkins(self):
        """Run scheduled health check-ins for all active users."""
        try:
            # Get all active users with care plans
            active_users = await self._get_active_users()
            for user_id in active_users:
                # Get user's care plan
                care_plans = await get_user_care_plans(self.db, user_id, status="active")
                if not care_plans:
                    continue

                # Perform health check
                risk_score, alerts = await self.check_health_status(user_id)
                
                # If high risk, trigger immediate notification
                if risk_score >= 0.7:
                    await self._send_health_alerts(user_id, alerts)
                    # Notify healthcare provider
                    await self._notify_healthcare_provider(user_id, risk_score, alerts)

        except Exception as e:
            logger.error(f"Error in scheduled health check-ins: {str(e)}")

    async def run_predictive_analysis(self):
        """Run weekly predictive analysis for all active users."""
        try:
            active_users = await self._get_active_users()
            for user_id in active_users:
                # Get historical data
                history = await self._get_health_history(user_id, days=90)  # 3 months of data
                if len(history) < 30:  # Need at least 30 days of data
                    continue

                # Run predictive analysis
                predictions = await self._predict_health_trends(history)
                
                # If concerning trends detected, schedule additional monitoring
                if predictions.get('risk_level') == 'high':
                    await self._schedule_additional_monitoring(user_id)

        except Exception as e:
            logger.error(f"Error in predictive analysis: {str(e)}")

    async def _predict_health_trends(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Predict future health trends using machine learning."""
        # Prepare training data
        X = self._prepare_metrics_matrix(history[:-7])  # Use all but last week for training
        y = self._prepare_target_metrics(history[7:])   # Use next week's data as target

        # Train predictive model
        self.predictive_model.fit(X, y)

        # Make predictions for next week
        last_week_data = self._prepare_metrics_matrix(history[-7:])
        predictions = self.predictive_model.predict(last_week_data)

        # Analyze predictions for concerning trends
        risk_level = self._analyze_predictions(predictions)
        
        return {
            "risk_level": risk_level,
            "predictions": predictions.tolist(),
            "confidence": self.predictive_model.score(X, y)
        }

    def _prepare_target_metrics(self, history: List[Dict[str, Any]]) -> np.ndarray:
        """Prepare target metrics for prediction."""
        targets = []
        for entry in history:
            targets.append([
                entry['health_metrics'].get('heart_rate', 0),
                entry['health_metrics'].get('blood_pressure', {}).get('systolic', 0),
                entry['health_metrics'].get('blood_pressure', {}).get('diastolic', 0),
                entry['health_metrics'].get('blood_sugar', 0)
            ])
        return np.array(targets)

    def _analyze_predictions(self, predictions: np.ndarray) -> str:
        """Analyze predictions to determine risk level."""
        # Calculate average predicted values
        avg_heart_rate = np.mean(predictions[:, 0])
        avg_systolic = np.mean(predictions[:, 1])
        avg_diastolic = np.mean(predictions[:, 2])
        avg_blood_sugar = np.mean(predictions[:, 3])

        # Determine risk level based on predicted values
        risk_factors = 0
        if avg_heart_rate > 100:
            risk_factors += 1
        if avg_systolic > 140 or avg_diastolic > 90:
            risk_factors += 1
        if avg_blood_sugar > 180:
            risk_factors += 1

        if risk_factors >= 2:
            return "high"
        elif risk_factors == 1:
            return "moderate"
        return "low"

    async def _schedule_additional_monitoring(self, user_id: int):
        """Schedule additional monitoring for high-risk users."""
        # Add more frequent check-ins
        self.scheduler.add_job(
            self.check_health_status,
            CronTrigger(hour='*/4'),  # Every 4 hours
            args=[user_id],
            id=f'additional_monitoring_{user_id}'
        )

    async def _notify_healthcare_provider(self, user_id: int, risk_score: float, alerts: List[str]):
        """Notify healthcare provider about high-risk situations."""
        # Get user's assigned healthcare provider
        user = await self._get_user_details(user_id)
        if user and user.get('practitioner_id'):
            await send_notification(
                user_id=user['practitioner_id'],
                title="High-Risk Patient Alert",
                message=f"Patient {user_id} has a high risk score ({risk_score:.2f}). Alerts: {', '.join(alerts)}",
                notification_type="provider_alert"
            )

    async def _get_active_users(self) -> List[int]:
        """Get list of active users with care plans."""
        result = await self.db.execute(
            select(CarePlan.user_id)
            .where(CarePlan.status == "active")
            .distinct()
        )
        return [row[0] for row in result.all()]

    async def _get_user_details(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user details including assigned healthcare provider."""
        result = await self.db.execute(
            select(User)
            .where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        return user.__dict__ if user else None

    async def analyze_health_patterns(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """
        Analyze health patterns and detect anomalies in user's health data.
        """
        # Get historical health data
        history = await self._get_health_history(user_id, days)
        if not history:
            return {"status": "insufficient_data"}

        # Extract metrics for analysis
        metrics_matrix = self._prepare_metrics_matrix(history)
        
        # Detect anomalies
        anomalies = self._detect_anomalies(metrics_matrix)
        
        # Analyze trends
        trends = self.predictive_analytics.analyze_health_trends(history)
        
        # Calculate risk factors
        risk_factors = await self._calculate_risk_factors(history)
        
        return {
            "anomalies": anomalies,
            "trends": trends,
            "risk_factors": risk_factors,
            "recommendations": self._generate_recommendations(anomalies, trends, risk_factors)
        }

    async def check_health_status(self, user_id: int) -> Tuple[float, List[str]]:
        """
        Check current health status and generate alerts if needed.
        """
        # Get recent check-ins
        recent_checkins = await self._get_health_history(user_id, days=7)
        if not recent_checkins:
            return 0.0, []

        # Calculate current risk score
        risk_score = await self._calculate_current_risk(recent_checkins[-1])
        
        # Generate alerts
        alerts = await self._generate_alerts(recent_checkins[-1], risk_score)
        
        # Send notifications if needed
        if alerts:
            await self._send_health_alerts(user_id, alerts)
        
        return risk_score, alerts

    async def _get_health_history(self, user_id: int, days: int) -> List[Dict[str, Any]]:
        """Get user's health check-in history."""
        result = await self.db.execute(
            select(HealthCheckIn)
            .where(
                and_(
                    HealthCheckIn.user_id == user_id,
                    HealthCheckIn.check_in_time >= datetime.utcnow() - timedelta(days=days)
                )
            )
            .order_by(HealthCheckIn.check_in_time.desc())
        )
        checkins = result.scalars().all()
        return [checkin.__dict__ for checkin in checkins]

    def _prepare_metrics_matrix(self, history: List[Dict[str, Any]]) -> np.ndarray:
        """Prepare metrics matrix for anomaly detection."""
        metrics = []
        for entry in history:
            metrics.append([
                entry['health_metrics'].get('heart_rate', 0),
                entry['health_metrics'].get('blood_pressure', {}).get('systolic', 0),
                entry['health_metrics'].get('blood_pressure', {}).get('diastolic', 0),
                entry['health_metrics'].get('blood_sugar', 0),
                entry['health_metrics'].get('temperature', 0),
                entry['health_metrics'].get('sleep_hours', 0),
                entry['health_metrics'].get('stress_level', 0),
                entry['health_metrics'].get('mood', 0)
            ])
        return np.array(metrics)

    def _detect_anomalies(self, metrics_matrix: np.ndarray) -> List[Dict[str, Any]]:
        """Detect anomalies in health metrics using Isolation Forest."""
        if len(metrics_matrix) < 10:  # Need minimum data points
            return []

        # Scale the data
        scaled_data = self.scaler.fit_transform(metrics_matrix)
        
        # Detect anomalies
        anomaly_scores = self.anomaly_detector.fit_predict(scaled_data)
        
        # Identify anomalous entries
        anomalies = []
        for i, score in enumerate(anomaly_scores):
            if score == -1:  # Anomaly detected
                anomalies.append({
                    "index": i,
                    "metrics": metrics_matrix[i].tolist(),
                    "severity": abs(self.anomaly_detector.score_samples([scaled_data[i]])[0])
                })
        
        return anomalies

    async def _calculate_risk_factors(self, history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Calculate risk factors based on health history."""
        risk_factors = []
        
        # Analyze vital signs trends
        vital_signs = self._analyze_vital_signs_trends(history)
        if vital_signs:
            risk_factors.extend(vital_signs)
        
        # Analyze lifestyle factors
        lifestyle = self._analyze_lifestyle_factors(history)
        if lifestyle:
            risk_factors.extend(lifestyle)
        
        # Analyze medication adherence
        medication = self._analyze_medication_adherence(history)
        if medication:
            risk_factors.append(medication)
        
        return risk_factors

    def _analyze_vital_signs_trends(self, history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze trends in vital signs."""
        trends = []
        
        # Heart rate trend
        heart_rates = [h['health_metrics'].get('heart_rate') for h in history if h['health_metrics'].get('heart_rate')]
        if heart_rates:
            avg_hr = sum(heart_rates) / len(heart_rates)
            if avg_hr > 100:
                trends.append({
                    "factor": "heart_rate",
                    "severity": "high",
                    "description": f"Elevated average heart rate: {avg_hr:.1f} bpm"
                })
        
        # Blood pressure trend
        systolic = [h['health_metrics'].get('blood_pressure', {}).get('systolic') for h in history]
        diastolic = [h['health_metrics'].get('blood_pressure', {}).get('diastolic') for h in history]
        
        if systolic and diastolic:
            avg_systolic = sum(systolic) / len(systolic)
            avg_diastolic = sum(diastolic) / len(diastolic)
            
            if avg_systolic > 140 or avg_diastolic > 90:
                trends.append({
                    "factor": "blood_pressure",
                    "severity": "high",
                    "description": f"Elevated blood pressure: {avg_systolic:.1f}/{avg_diastolic:.1f}"
                })
        
        return trends

    def _analyze_lifestyle_factors(self, history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze lifestyle factors."""
        factors = []
        
        # Sleep analysis
        sleep_hours = [h['health_metrics'].get('sleep_hours') for h in history if h['health_metrics'].get('sleep_hours')]
        if sleep_hours:
            avg_sleep = sum(sleep_hours) / len(sleep_hours)
            if avg_sleep < 6:
                factors.append({
                    "factor": "sleep",
                    "severity": "moderate",
                    "description": f"Insufficient average sleep: {avg_sleep:.1f} hours"
                })
        
        # Stress analysis
        stress_levels = [h['health_metrics'].get('stress_level') for h in history if h['health_metrics'].get('stress_level')]
        if stress_levels:
            avg_stress = sum(stress_levels) / len(stress_levels)
            if avg_stress >= 4:
                factors.append({
                    "factor": "stress",
                    "severity": "high",
                    "description": f"High average stress level: {avg_stress:.1f}/5"
                })
        
        return factors

    def _analyze_medication_adherence(self, history: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Analyze medication adherence."""
        adherence = [h['health_metrics'].get('medication_taken') for h in history if h['health_metrics'].get('medication_taken') is not None]
        
        if adherence:
            adherence_rate = sum(adherence) / len(adherence)
            if adherence_rate < 0.8:  # Less than 80% adherence
                return {
                    "factor": "medication_adherence",
                    "severity": "high",
                    "description": f"Low medication adherence: {adherence_rate:.1%}"
                }
        
        return None

    async def _calculate_current_risk(self, latest_checkin: Dict[str, Any]) -> float:
        """Calculate current risk score based on latest check-in."""
        risk_score = 0.0
        metrics = latest_checkin['health_metrics']
        
        # Heart rate risk
        if metrics.get('heart_rate'):
            if metrics['heart_rate'] > 100:
                risk_score += 0.3
            elif metrics['heart_rate'] < 60:
                risk_score += 0.2
        
        # Blood pressure risk
        if metrics.get('blood_pressure'):
            systolic = metrics['blood_pressure'].get('systolic')
            diastolic = metrics['blood_pressure'].get('diastolic')
            if systolic and diastolic:
                if systolic > 140 or diastolic > 90:
                    risk_score += 0.4
                elif systolic < 90 or diastolic < 60:
                    risk_score += 0.3
        
        # Blood sugar risk
        if metrics.get('blood_sugar'):
            if metrics['blood_sugar'] > 180:
                risk_score += 0.4
            elif metrics['blood_sugar'] < 70:
                risk_score += 0.5
        
        # Temperature risk
        if metrics.get('temperature'):
            if metrics['temperature'] > 37.5:
                risk_score += 0.4
        
        # Mood and stress risk
        if metrics.get('mood') and metrics.get('stress_level'):
            if metrics['mood'] <= 2 or metrics['stress_level'] >= 4:
                risk_score += 0.3
        
        return min(risk_score, 1.0)

    async def _generate_alerts(self, checkin: Dict[str, Any], risk_score: float) -> List[str]:
        """Generate health alerts based on check-in data and risk score."""
        alerts = []
        metrics = checkin['health_metrics']
        
        if risk_score >= 0.7:
            alerts.append("High risk detected - Immediate medical attention recommended")
        
        if metrics.get('heart_rate'):
            if metrics['heart_rate'] > 100:
                alerts.append("Elevated heart rate detected")
            elif metrics['heart_rate'] < 60:
                alerts.append("Low heart rate detected")
        
        if metrics.get('blood_pressure'):
            systolic = metrics['blood_pressure'].get('systolic')
            diastolic = metrics['blood_pressure'].get('diastolic')
            if systolic and diastolic:
                if systolic > 140 or diastolic > 90:
                    alerts.append("High blood pressure detected")
                elif systolic < 90 or diastolic < 60:
                    alerts.append("Low blood pressure detected")
        
        if metrics.get('blood_sugar'):
            if metrics['blood_sugar'] > 180:
                alerts.append("High blood sugar detected")
            elif metrics['blood_sugar'] < 70:
                alerts.append("Low blood sugar detected")
        
        if metrics.get('temperature') and metrics['temperature'] > 37.5:
            alerts.append("Elevated temperature detected")
        
        if metrics.get('mood') and metrics['mood'] <= 2:
            alerts.append("Low mood detected - Consider reaching out for support")
        
        if metrics.get('stress_level') and metrics['stress_level'] >= 4:
            alerts.append("High stress level detected - Consider stress management techniques")
        
        return alerts

    async def _send_health_alerts(self, user_id: int, alerts: List[str]):
        """Send health alerts to user."""
        for alert in alerts:
            await send_notification(
                user_id=user_id,
                title="Health Alert",
                message=alert,
                notification_type="health_alert"
            )

    def _generate_recommendations(
        self,
        anomalies: List[Dict[str, Any]],
        trends: Dict[str, Any],
        risk_factors: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate personalized health recommendations."""
        recommendations = []
        
        # Add recommendations based on anomalies
        for anomaly in anomalies:
            if anomaly['severity'] > 0.8:
                recommendations.append("Schedule a consultation with your healthcare provider")
        
        # Add recommendations based on trends
        if trends.get('risk_level') == 'high':
            recommendations.extend(trends.get('recommendations', []))
        
        # Add recommendations based on risk factors
        for factor in risk_factors:
            if factor['severity'] == 'high':
                if factor['factor'] == 'heart_rate':
                    recommendations.append("Monitor your heart rate closely and avoid strenuous activities")
                elif factor['factor'] == 'blood_pressure':
                    recommendations.append("Monitor your blood pressure regularly and maintain a low-sodium diet")
                elif factor['factor'] == 'stress':
                    recommendations.append("Consider stress management techniques or professional support")
                elif factor['factor'] == 'medication_adherence':
                    recommendations.append("Set up medication reminders and maintain a consistent schedule")
        
        return list(set(recommendations))  # Remove duplicates 