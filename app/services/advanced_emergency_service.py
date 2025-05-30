from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload
from app.db.models.emergency_response import (
    EmergencyResponse,
    EmergencyResource,
    EmergencyProtocol,
    EmergencyTeam,
    EmergencyZone,
    EmergencyDispatch,
    EmergencyTracking,
    EmergencyResourceInventory,
    team_members
)
from app.schemas.emergency_response import (
    EmergencyResponseCreate,
    EmergencyResourceCreate,
    EmergencyProtocolCreate,
    EmergencyTeamCreate,
    EmergencyZoneCreate,
    EmergencyDispatchCreate,
    EmergencyTrackingCreate,
    EmergencyResourceInventoryCreate,
    EmergencyAnalytics
)
from app.services.notification_service import send_notification
from app.services.ai_services import classify_emergency_type
from app.core.config import settings
import logging
import math
import asyncio
from geopy.distance import geodesic
import aiohttp
import json

logger = logging.getLogger(__name__)

class AdvancedEmergencyService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.active_emergencies: Dict[int, EmergencyTracking] = {}
        self.emergency_zones: Dict[int, EmergencyZone] = {}
        self.resource_locations: Dict[int, Tuple[float, float]] = {}
        self.last_sync_time: Optional[datetime] = None
        self.sync_status: str = "not_initialized"

    async def get_all_emergency_zones(self) -> List[EmergencyZone]:
        """Get all emergency zones from the database."""
        try:
            result = await self.db.execute(select(EmergencyZone))
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting emergency zones: {str(e)}")
            return []

    async def get_all_resources(self) -> List[EmergencyResource]:
        """Get all emergency resources from the database."""
        try:
            result = await self.db.execute(select(EmergencyResource))
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting emergency resources: {str(e)}")
            return []

    async def get_sync_status(self) -> Dict[str, Any]:
        """Get the current synchronization status of the emergency system."""
        try:
            # Get counts from database
            zones_count = len(self.emergency_zones)
            resources_count = len(self.resource_locations)
            active_emergencies_count = len(self.active_emergencies)

            # Get total counts from database
            zones_result = await self.db.execute(select(func.count(EmergencyZone.id)))
            total_zones = zones_result.scalar() or 0

            resources_result = await self.db.execute(select(func.count(EmergencyResource.id)))
            total_resources = resources_result.scalar() or 0

            active_emergencies_result = await self.db.execute(
                select(func.count(EmergencyResponse.id)).where(
                    EmergencyResponse.status.in_(["initialized", "in_progress"])
                )
            )
            total_active_emergencies = active_emergencies_result.scalar() or 0

            return {
                "status": self.sync_status,
                "last_sync_time": self.last_sync_time.isoformat() if self.last_sync_time else None,
                "zones": {
                    "loaded": zones_count,
                    "total": total_zones,
                    "sync_percentage": (zones_count / total_zones * 100) if total_zones > 0 else 0
                },
                "resources": {
                    "loaded": resources_count,
                    "total": total_resources,
                    "sync_percentage": (resources_count / total_resources * 100) if total_resources > 0 else 0
                },
                "active_emergencies": {
                    "tracked": active_emergencies_count,
                    "total": total_active_emergencies,
                    "sync_percentage": (active_emergencies_count / total_active_emergencies * 100) if total_active_emergencies > 0 else 0
                }
            }
        except Exception as e:
            logger.error(f"Error getting sync status: {str(e)}")
            raise

    async def initialize_emergency_system(self):
        """Initialize the emergency system with current resources and zones."""
        try:
            # Load active emergency zones
            zones = await self.get_all_emergency_zones()
            for zone in zones:
                self.emergency_zones[zone.id] = zone

            # Load resource locations
            resources = await self.get_all_resources()
            for resource in resources:
                if resource.location_lat and resource.location_lon:
                    self.resource_locations[resource.id] = (resource.location_lat, resource.location_lon)

            # Update sync status
            self.last_sync_time = datetime.now()
            self.sync_status = "initialized"
            
            logger.info(f"Emergency system initialized with {len(zones)} zones and {len(resources)} resources")
            return True
        except Exception as e:
            self.sync_status = "error"
            logger.error(f"Error initializing emergency system: {str(e)}")
            raise

    async def create_emergency_response(
        self,
        response_data: EmergencyResponseCreate
    ) -> EmergencyResponse:
        """Create and initialize a new emergency response with advanced tracking."""
        try:
            # Create emergency response record
            response = EmergencyResponse(**response_data.dict())
            self.db.add(response)
            await self.db.commit()
            await self.db.refresh(response)

            # Initialize tracking
            tracking = EmergencyTracking(
                emergency_id=response.id,
                status="initialized",
                location_lat=response.location_lat,
                location_lon=response.location_lon,
                last_updated=datetime.utcnow()
            )
            self.db.add(tracking)
            await self.db.commit()

            # Store in active emergencies
            self.active_emergencies[response.id] = tracking


            # Find and allocate resources
            resources = await self.allocate_resources(
                response.location_lat,
                response.location_lon,
                response.emergency_type,
            )

            # Create dispatch records
            for resource in resources:
                dispatch = EmergencyDispatch(
                    emergency_id=response.id,
                    resource_id=resource.id,
                    status="dispatched",
                    dispatch_time=datetime.utcnow()
                )
                self.db.add(dispatch)

            await self.db.commit()

            # Send notifications
            await self._send_emergency_notifications(response, resources)

            return response

        except Exception as e:
            logger.error(f"Error creating emergency response: {str(e)}")
            raise

    async def allocate_resources(
        self,
        lat: float,
        lon: float,
        emergency_type: str,
        weather: Dict,
        traffic: Dict
    ) -> List[EmergencyResource]:
        """Smart resource allocation based on multiple factors."""
        try:
            # Get all available resources
            resources = await self.get_available_resources(emergency_type)
            
            # Calculate scores for each resource
            scored_resources = []
            for resource in resources:
                score = await self._calculate_resource_score(
                    resource,
                    lat,
                    lon,
                    weather,
                    traffic
                )
                scored_resources.append((resource, score))

            # Sort by score and select top resources
            scored_resources.sort(key=lambda x: x[1], reverse=True)
            selected_resources = [r[0] for r in scored_resources[:3]]  # Select top 3

            # Update resource status
            for resource in selected_resources:
                resource.availability = False
                resource.current_emergency_id = emergency_type

            await self.db.commit()
            return selected_resources

        except Exception as e:
            logger.error(f"Error allocating resources: {str(e)}")
            raise

    async def _calculate_resource_score(
        self,
        resource: EmergencyResource,
        target_lat: float,
        target_lon: float,
        weather: Dict,
        traffic: Dict
    ) -> float:
        """Calculate resource allocation score based on multiple factors."""
        try:
            # Distance score (closer is better)
            distance = geodesic(
                (resource.location_lat, resource.location_lon),
                (target_lat, target_lon)
            ).kilometers
            distance_score = 1 / (1 + distance)

            # Weather impact score
            weather_score = self._calculate_weather_impact(weather)

            # Traffic impact score
            traffic_score = self._calculate_traffic_impact(traffic)

            # Resource capability score
            capability_score = resource.capability_score if hasattr(resource, 'capability_score') else 0.5

            # Calculate final score
            final_score = (
                distance_score * 0.4 +
                weather_score * 0.2 +
                traffic_score * 0.2 +
                capability_score * 0.2
            )

            return final_score

        except Exception as e:
            logger.error(f"Error calculating resource score: {str(e)}")
            return 0.0

    async def update_emergency_tracking(
        self,
        emergency_id: int,
        tracking_data: EmergencyTrackingCreate
    ) -> EmergencyTracking:
        """Update emergency tracking information."""
        try:
            tracking = self.active_emergencies.get(emergency_id)
            if not tracking:
                raise ValueError(f"No active tracking for emergency {emergency_id}")

            # Update tracking data
            for key, value in tracking_data.dict().items():
                setattr(tracking, key, value)
            tracking.last_updated = datetime.utcnow()

            await self.db.commit()
            await self.db.refresh(tracking)

            # Check if emergency is in any defined zones
            await self._check_emergency_zones(tracking)

            return tracking

        except Exception as e:
            logger.error(f"Error updating emergency tracking: {str(e)}")
            raise

    async def _check_emergency_zones(self, tracking: EmergencyTracking):
        """Check if emergency is in any defined zones and trigger appropriate actions."""
        for zone in self.emergency_zones.values():
            if self._is_point_in_zone(
                tracking.location_lat,
                tracking.location_lon,
                zone
            ):
                await self._handle_zone_entry(tracking, zone)

    def _is_point_in_zone(
        self,
        lat: float,
        lon: float,
        zone: EmergencyZone
    ) -> bool:
        """Check if a point is within an emergency zone."""
        # Simple circular zone check
        center_distance = geodesic(
            (lat, lon),
            (zone.center_lat, zone.center_lon)
        ).kilometers
        return center_distance <= zone.radius_km

    async def _handle_zone_entry(
        self,
        tracking: EmergencyTracking,
        zone: EmergencyZone
    ):
        """Handle emergency entry into a defined zone."""
        # Update zone status
        zone.active_emergencies += 1
        await self.db.commit()

        # Trigger zone-specific protocols
        if zone.protocol:
            await self._execute_zone_protocol(tracking, zone)

        # Send notifications
        await self._send_zone_notifications(tracking, zone)

    async def get_emergency_analytics(self) -> EmergencyAnalytics:
        """Generate comprehensive emergency response analytics."""
        try:
            # Get all emergencies with their dispatches and resources
            stmt = select(EmergencyResponse).options(
                selectinload(EmergencyResponse.dispatches).selectinload(EmergencyDispatch.resource)
            )
            result = await self.db.execute(stmt)
            emergencies = result.scalars().all()

            # Calculate response metrics
            response_times = []
            resolution_times = []
            resource_utilization = {}

            for emergency in emergencies:
                # Calculate response time
                if emergency.dispatched_at and emergency.created_at:
                    response_time = (emergency.dispatched_at - emergency.created_at).total_seconds()
                    response_times.append(response_time)

                # Calculate resolution time
                if emergency.resolved_at and emergency.created_at:
                    resolution_time = (emergency.resolved_at - emergency.created_at).total_seconds()
                    resolution_times.append(resolution_time)

                # Track resource utilization
                for dispatch in emergency.dispatches:
                    if dispatch.resource and dispatch.resource.type:
                        resource_type = dispatch.resource.type
                        if resource_type not in resource_utilization:
                            resource_utilization[resource_type] = 0
                        resource_utilization[resource_type] += 1

            # Calculate statistics
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            avg_resolution_time = sum(resolution_times) / len(resolution_times) if resolution_times else 0

            return EmergencyAnalytics(
                total_emergencies=len(emergencies),
                average_response_time=avg_response_time,
                average_resolution_time=avg_resolution_time,
                resource_utilization=resource_utilization,
                emergency_types=self._calculate_emergency_type_distribution(emergencies),
                zone_activity=self._calculate_zone_activity(emergencies)
            )

        except Exception as e:
            logger.error(f"Error generating emergency analytics: {str(e)}")
            raise

    def _calculate_emergency_type_distribution(
        self,
        emergencies: List[EmergencyResponse]
    ) -> Dict[str, int]:
        """Calculate distribution of emergency types."""
        distribution = {}
        for emergency in emergencies:
            if emergency.emergency_type not in distribution:
                distribution[emergency.emergency_type] = 0
            distribution[emergency.emergency_type] += 1
        return distribution

    def _calculate_zone_activity(
        self,
        emergencies: List[EmergencyResponse]
    ) -> Dict[int, int]:
        """Calculate emergency activity by zone."""
        zone_activity = {}
        for emergency in emergencies:
            for zone in self.emergency_zones.values():
                if self._is_point_in_zone(
                    emergency.location_lat,
                    emergency.location_lon,
                    zone
                ):
                    if zone.id not in zone_activity:
                        zone_activity[zone.id] = 0
                    zone_activity[zone.id] += 1
        return zone_activity

    async def _send_emergency_notifications(
        self,
        emergency: EmergencyResponse,
        resources: List[EmergencyResource]
    ):
        """Send notifications to all relevant parties."""
        # Notify emergency response team
        await send_notification(
            user_id=emergency.user_id,
            title="Emergency Response Initiated",
            message=f"Emergency response has been initiated for {emergency.emergency_type} emergency.",
            notification_type="emergency"
        )

        # Notify allocated resources
        for resource in resources:
            await send_notification(
                user_id=resource.assigned_user_id,
                title="Emergency Dispatch",
                message=f"You have been dispatched to an emergency at {emergency.location_lat}, {emergency.location_lon}",
                notification_type="dispatch"
            )

    async def _send_zone_notifications(
        self,
        tracking: EmergencyTracking,
        zone: EmergencyZone
    ):
        """Send notifications for zone entry."""
        await send_notification(
            user_id=tracking.emergency.user_id,
            title="Entered Emergency Zone",
            message=f"Emergency has entered {zone.name} zone. Additional protocols activated.",
            notification_type="zone"
        )

    def _calculate_weather_impact(self, weather: Dict) -> float:
        """Calculate weather impact score for resource allocation."""
        # Implement weather impact calculation based on conditions
        return 1.0  # Placeholder

    def _calculate_traffic_impact(self, traffic: Dict) -> float:
        """Calculate traffic impact score for resource allocation."""
        # Implement traffic impact calculation based on conditions
        return 1.0  # Placeholder

    async def create_emergency_team(
        self,
        team_data: EmergencyTeamCreate
    ) -> EmergencyTeam:
        """Create a new emergency response team."""
        try:
            # Create the team
            team = EmergencyTeam(
                name=team_data.name,
                type=team_data.type,
                leader_id=team_data.leader_id,
                status="active"
            )
            self.db.add(team)
            await self.db.commit()
            await self.db.refresh(team)

            # Add team members
            if team_data.member_ids:
                for member_id in team_data.member_ids:
                    # Add member to team_members association table
                    stmt = team_members.insert().values(
                        team_id=team.id,
                        user_id=member_id
                    )
                    await self.db.execute(stmt)
                await self.db.commit()

            # Send notifications
            await send_notification(
                user_id=team.leader_id,
                title="Team Leadership Assignment",
                message=f"You have been assigned as leader of team {team.name}",
                notification_type="team"
            )

            for member_id in team_data.member_ids:
                await send_notification(
                    user_id=member_id,
                    title="Team Assignment",
                    message=f"You have been added to team {team.name}",
                    notification_type="team"
                )

            return team

        except Exception as e:
            logger.error(f"Error creating emergency team: {str(e)}")
            raise

    async def create_emergency_zone(
        self,
        zone_data: EmergencyZoneCreate
    ) -> EmergencyZone:
        """Create a new emergency zone with specific protocols."""
        try:
            # Create the zone
            zone = EmergencyZone(
                name=zone_data.name,
                center_lat=zone_data.center_lat,
                center_lon=zone_data.center_lon,
                radius_km=zone_data.radius_km,
                type=zone_data.type,
                protocol=zone_data.protocol,
                active_emergencies=0
            )
            self.db.add(zone)
            await self.db.commit()
            await self.db.refresh(zone)

            # Add to active zones
            self.emergency_zones[zone.id] = zone

            # Send notifications to nearby resources
            nearby_resources = await self._get_resources_in_zone(zone)
            for resource in nearby_resources:
                if resource.assigned_user_id:
                    await send_notification(
                        user_id=resource.assigned_user_id,
                        title="New Emergency Zone Created",
                        message=f"A new emergency zone '{zone.name}' has been created in your area",
                        notification_type="zone"
                    )

            return zone

        except Exception as e:
            logger.error(f"Error creating emergency zone: {str(e)}")
            raise

    async def _get_resources_in_zone(self, zone: EmergencyZone) -> List[EmergencyResource]:
        """Get all emergency resources within a zone."""
        try:
            result = await self.db.execute(
                select(EmergencyResource).where(
                    and_(
                        EmergencyResource.location_lat.isnot(None),
                        EmergencyResource.location_lon.isnot(None)
                    )
                )
            )
            resources = result.scalars().all()
            
            # Filter resources that are within the zone
            return [
                resource for resource in resources
                if self._is_point_in_zone(
                    resource.location_lat,
                    resource.location_lon,
                    zone
                )
            ]
        except Exception as e:
            logger.error(f"Error getting resources in zone: {str(e)}")
            return []

    async def create_emergency_dispatch(
        self,
        dispatch_data: EmergencyDispatchCreate
    ) -> EmergencyDispatch:
        """Create a new emergency dispatch record."""
        try:
            # Create the dispatch record
            dispatch = EmergencyDispatch(
                emergency_id=dispatch_data.emergency_id,
                resource_id=dispatch_data.resource_id,
                status=dispatch_data.status,
                notes=dispatch_data.notes,
                dispatch_time=datetime.now()
            )
            self.db.add(dispatch)
            await self.db.commit()
            await self.db.refresh(dispatch)

            # Update resource status if needed
            if dispatch.status == "dispatched":
                resource = await self.db.get(EmergencyResource, dispatch.resource_id)
                if resource:
                    resource.availability = False
                    resource.current_emergency_id = dispatch.emergency_id
                    await self.db.commit()

            # Send notifications
            emergency = await self.db.get(EmergencyResponse, dispatch.emergency_id)
            resource = await self.db.get(EmergencyResource, dispatch.resource_id)
            
            if emergency and resource:
                # Notify emergency creator
                await send_notification(
                    user_id=emergency.user_id,
                    title="Emergency Resource Dispatched",
                    message=f"Resource {resource.name} has been dispatched to your emergency",
                    notification_type="dispatch"
                )

                # Notify resource user if assigned
                if resource.assigned_user_id:
                    await send_notification(
                        user_id=resource.assigned_user_id,
                        title="Emergency Dispatch Assignment",
                        message=f"You have been dispatched to emergency #{emergency.id}",
                        notification_type="dispatch"
                    )

            return dispatch

        except Exception as e:
            logger.error(f"Error creating emergency dispatch: {str(e)}")
            raise

    async def create_resource_inventory(
        self,
        inventory_data: EmergencyResourceInventoryCreate
    ) -> EmergencyResourceInventory:
        """Create a new emergency resource inventory record."""
        try:
            # Create the inventory record
            inventory = EmergencyResourceInventory(
                resource_id=inventory_data.resource_id,
                item_type=inventory_data.item_type,
                quantity=inventory_data.quantity,
                minimum_quantity=inventory_data.minimum_quantity,
                maximum_quantity=inventory_data.maximum_quantity,
                notes=inventory_data.notes,
                last_restocked=datetime.now()
            )
            self.db.add(inventory)
            await self.db.commit()
            await self.db.refresh(inventory)

            # Update resource status if needed
            resource = await self.db.get(EmergencyResource, inventory_data.resource_id)
            if resource:
                resource.inventory_status = "updated"
                await self.db.commit()

            # Send notifications to resource manager
            if resource and resource.assigned_user_id:
                await send_notification(
                    user_id=resource.assigned_user_id,
                    title="Resource Inventory Updated",
                    message=f"Inventory for resource {resource.name} has been updated",
                    notification_type="inventory"
                )

            return inventory

        except Exception as e:
            logger.error(f"Error creating resource inventory: {str(e)}")
            raise 