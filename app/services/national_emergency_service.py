from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.schemas.national_emergency import (
    EmergencyAlert,
    EmergencyAlertType,
    EmergencySeverity,
    EmergencyRegion,
    EmergencyResource,
    EmergencyAlertRequest,
    EmergencyAlertResponse,
    EmergencyAlertSubscription
)
from app.db.models.national_emergency import (
    EmergencyAlert as EmergencyAlertModel,
    EmergencyAlertSubscription as EmergencyAlertSubscriptionModel,
    NationalEmergencyResource as NationalEmergencyResourceModel,
    EmergencyRegion as EmergencyRegionModel
)
import logging
from datetime import datetime
import math
import aiohttp
from app.core.config import settings

logger = logging.getLogger(__name__)

class NationalEmergencyService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.emergency_api_url = settings.EMERGENCY_API_URL
        self.emergency_api_key = settings.EMERGENCY_API_KEY

    async def get_active_alerts(
        self,
        request: EmergencyAlertRequest
    ) -> EmergencyAlertResponse:
        """Get active emergency alerts for a location."""
        try:
            # Get alerts from external API
            external_alerts = await self._fetch_external_alerts(request)
            
            # Get alerts from database
            db_alerts = await self._get_db_alerts(request)
            
            # Combine and filter alerts
            all_alerts = external_alerts + db_alerts
            filtered_alerts = self._filter_alerts_by_location(
                all_alerts,
                request.location,
                request.radius_km
            )
            
            # Get nearby resources
            resources = await self._get_nearby_resources(
                request.location,
                request.radius_km
            )
            
            return EmergencyAlertResponse(
                user_id=request.user_id,
                active_alerts=filtered_alerts,
                nearby_resources=resources,
                recommended_actions=self._generate_recommended_actions(filtered_alerts),
                emergency_contacts=self._get_emergency_contacts(request.location),
                last_updated=datetime.utcnow()
            )
        except Exception as e:
            logger.error(f"Failed to get active alerts: {str(e)}")
            raise

    async def create_alert_subscription(
        self,
        user_id: int,
        subscription_data: EmergencyAlertSubscription
    ) -> EmergencyAlertSubscriptionModel:
        """Create a new emergency alert subscription."""
        try:
            subscription = EmergencyAlertSubscriptionModel(
                user_id=user_id,
                alert_types=subscription_data.alert_types,
                regions=subscription_data.regions,
                severity_threshold=subscription_data.severity_threshold,
                notification_preferences=subscription_data.notification_preferences
            )
            self.db.add(subscription)
            await self.db.commit()
            await self.db.refresh(subscription)
            return subscription
        except Exception as e:
            logger.error(f"Failed to create alert subscription: {str(e)}")
            raise

    async def _fetch_external_alerts(
        self,
        request: EmergencyAlertRequest
    ) -> List[EmergencyAlert]:
        """Fetch alerts from external emergency alert API."""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {self.emergency_api_key}"}
                params = {
                    "lat": request.location["latitude"],
                    "lon": request.location["longitude"],
                    "radius": request.radius_km
                }
                
                async with session.get(
                    f"{self.emergency_api_url}/alerts",
                    headers=headers,
                    params=params
                ) as response:
                    if response.status != 200:
                        raise ValueError(f"Failed to fetch alerts: {await response.text()}")
                    
                    data = await response.json()
                    return [
                        EmergencyAlert(
                            alert_id=alert["id"],
                            type=alert["type"],
                            severity=alert["severity"],
                            title=alert["title"],
                            description=alert["description"],
                            affected_regions=alert["affected_regions"],
                            start_time=datetime.fromisoformat(alert["start_time"]),
                            end_time=datetime.fromisoformat(alert["end_time"]) if alert.get("end_time") else None,
                            source=alert["source"],
                            official_guidance=alert["official_guidance"],
                            resources=alert["resources"],
                            status=alert["status"]
                        )
                        for alert in data["alerts"]
                    ]
        except Exception as e:
            logger.error(f"Failed to fetch external alerts: {str(e)}")
            return []

    async def _get_db_alerts(
        self,
        request: EmergencyAlertRequest
    ) -> List[EmergencyAlert]:
        """Get alerts from the database."""
        try:
            result = await self.db.execute(
                select(EmergencyAlertModel)
                .where(EmergencyAlertModel.status == "active")
            )
            alerts = result.scalars().all()
            
            return [
                EmergencyAlert(
                    alert_id=alert.alert_id,
                    type=alert.type,
                    severity=alert.severity,
                    title=alert.title,
                    description=alert.description,
                    affected_regions=alert.affected_regions,
                    start_time=alert.start_time,
                    end_time=alert.end_time,
                    source=alert.source,
                    official_guidance=alert.official_guidance,
                    resources=alert.resources,
                    status=alert.status
                )
                for alert in alerts
            ]
        except Exception as e:
            logger.error(f"Failed to get database alerts: {str(e)}")
            return []

    def _filter_alerts_by_location(
        self,
        alerts: List[EmergencyAlert],
        location: Dict[str, float],
        radius_km: float
    ) -> List[EmergencyAlert]:
        """Filter alerts by location and radius."""
        filtered_alerts = []
        for alert in alerts:
            for region in alert.affected_regions:
                if region.coordinates:
                    distance = self._calculate_distance(
                        location["latitude"],
                        location["longitude"],
                        region.coordinates["latitude"],
                        region.coordinates["longitude"]
                    )
                    if distance <= radius_km:
                        filtered_alerts.append(alert)
                        break
        return filtered_alerts

    async def _get_nearby_resources(
        self,
        location: Dict[str, float],
        radius_km: float
    ) -> List[EmergencyResource]:
        """Get emergency resources near the location."""
        try:
            result = await self.db.execute(
                select(NationalEmergencyResourceModel)
                .where(NationalEmergencyResourceModel.is_active == True)
            )
            resources = result.scalars().all()
            
            nearby_resources = []
            for resource in resources:
                if resource.latitude and resource.longitude:
                    distance = self._calculate_distance(
                        location["latitude"],
                        location["longitude"],
                        resource.latitude,
                        resource.longitude
                    )
                    if distance <= radius_km:
                        nearby_resources.append(
                            EmergencyResource(
                                name=resource.name,
                                type=resource.type,
                                contact=resource.contact,
                                description=resource.description,
                                location=resource.location,
                                capacity=resource.capacity,
                                status=resource.status
                            )
                        )
            return nearby_resources
        except Exception as e:
            logger.error(f"Failed to get nearby resources: {str(e)}")
            return []

    def _calculate_distance(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:
        """Calculate distance between two points in kilometers."""
        R = 6371  # Earth's radius in kilometers
        
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = R * c
        
        return distance

    def _generate_recommended_actions(
        self,
        alerts: List[EmergencyAlert]
    ) -> List[str]:
        """Generate recommended actions based on active alerts."""
        actions = []
        for alert in alerts:
            actions.extend(alert.official_guidance)
        return list(set(actions))  # Remove duplicates

    def _get_emergency_contacts(
        self,
        location: Dict[str, float]
    ) -> List[Dict[str, str]]:
        """Get emergency contacts for the location."""
        # This would typically come from a database of emergency contacts
        # For now, returning a sample list
        return [
            {"name": "Emergency Services", "contact": "911"},
            {"name": "Local Hospital", "contact": "123-456-7890"},
            {"name": "Poison Control", "contact": "1-800-222-1222"}
        ] 