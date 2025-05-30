from datetime import datetime, timedelta
from typing import List, Optional, Dict, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
import aiohttp
import os
from app.db.models.emergency_response import (
    EmergencyResponse,
    EmergencyResource,
    EmergencyProtocol,
    EmergencyTraining,
    EmergencyType,
    EmergencySeverity
)
from app.schemas.emergency_response import (
    EmergencyResponseCreate,
    EmergencyResourceCreate,
    EmergencyProtocolCreate,
    EmergencyTrainingCreate,
)
from app.services.notification_service import send_notification
from app.services.ai_services import classify_emergency_type
import logging
import math

logger = logging.getLogger(__name__)

# Google Maps API configuration
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
GOOGLE_MAPS_BASE_URL = "https://maps.googleapis.com/maps/api"

class GoogleMapsService:
    def __init__(self, api_key: str = GOOGLE_MAPS_API_KEY):
        self.api_key = api_key
        self.base_url = GOOGLE_MAPS_BASE_URL

    async def get_geocode(self, address: str) -> Optional[Dict[str, float]]:
        """Get geocoding information for an address."""
        async with aiohttp.ClientSession() as session:
            params = {
                "address": address,
                "key": self.api_key
            }
            async with session.get(f"{self.base_url}/geocode/json", params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data["status"] == "OK":
                        location = data["results"][0]["geometry"]["location"]
                        return {
                            "lat": location["lat"],
                            "lng": location["lng"]
                        }
                return None

    async def get_distance_matrix(
        self,
        origins: List[Tuple[float, float]],
        destinations: List[Tuple[float, float]]
    ) -> Optional[List[Dict]]:
        """Get distance and duration between multiple origins and destinations."""
        async with aiohttp.ClientSession() as session:
            origins_str = "|".join([f"{lat},{lng}" for lat, lng in origins])
            destinations_str = "|".join([f"{lat},{lng}" for lat, lng in destinations])
            
            params = {
                "origins": origins_str,
                "destinations": destinations_str,
                "key": self.api_key
            }
            
            async with session.get(f"{self.base_url}/distancematrix/json", params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data["status"] == "OK":
                        return data["rows"]
                return None

    async def get_route(
        self,
        origin: Tuple[float, float],
        destination: Tuple[float, float],
        mode: str = "driving"
    ) -> Optional[Dict]:
        """Get detailed route information between two points."""
        async with aiohttp.ClientSession() as session:
            params = {
                "origin": f"{origin[0]},{origin[1]}",
                "destination": f"{destination[0]},{destination[1]}",
                "mode": mode,
                "key": self.api_key
            }
            
            async with session.get(f"{self.base_url}/directions/json", params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data["status"] == "OK":
                        return data["routes"][0]
                return None

# Initialize Google Maps service
maps_service = GoogleMapsService()

async def create_emergency_response(
    db: AsyncSession,
    response_data: EmergencyResponseCreate
) -> EmergencyResponse:
    """Create a new emergency response record."""
    response = EmergencyResponse(**response_data.dict())
    db.add(response)
    await db.commit()
    await db.refresh(response)
    
    # Send notifications
    await send_notification(
        user_id=response.user_id,
        title="Emergency Response Initiated",
        message=f"Emergency response has been initiated for {response.emergency_type.value} emergency.",
        notification_type="emergency"
    )
    
    return response

async def get_emergency_response(
    db: AsyncSession,
    response_id: int
) -> Optional[EmergencyResponse]:
    """Get emergency response details."""
    result = await db.execute(
        select(EmergencyResponse).where(EmergencyResponse.id == response_id)
    )
    return result.scalars().first()

async def update_emergency_response(
    db: AsyncSession,
    response_id: int,
    update_data: Dict
) -> Optional[EmergencyResponse]:
    """Update emergency response status and details."""
    response = await get_emergency_response(db, response_id)
    if not response:
        return None
    
    for key, value in update_data.items():
        setattr(response, key, value)
    
    await db.commit()
    await db.refresh(response)
    return response

async def get_nearby_resources(
    db: AsyncSession,
    lat: float,
    lon: float,
    radius_km: float = 10.0,
    resource_type: Optional[str] = None
) -> List[EmergencyResource]:
    """Get emergency resources within specified radius using Google Maps API."""
    query = select(EmergencyResource).where(EmergencyResource.availability == True)
    
    if resource_type:
        query = query.where(EmergencyResource.type == resource_type)
    
    result = await db.execute(query)
    resources = result.scalars().all()
    
    # Get distance matrix for all resources
    origins = [(lat, lon)]
    destinations = [(r.location_lat, r.location_lon) for r in resources if r.location_lat and r.location_lon]
    
    if not destinations:
        return []
    
    distance_matrix = await maps_service.get_distance_matrix(origins, destinations)
    
    # Filter resources based on distance
    nearby_resources = []
    if distance_matrix and distance_matrix[0]["elements"]:
        for i, element in enumerate(distance_matrix[0]["elements"]):
            if element["status"] == "OK":
                distance_km = element["distance"]["value"] / 1000  # Convert meters to kilometers
                if distance_km <= radius_km:
                    nearby_resources.append(resources[i])
    
    return nearby_resources

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in kilometers."""
    R = 6371  # Earth's radius in kilometers
    
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c

async def get_appropriate_protocol(
    db: AsyncSession,
    emergency_type: EmergencyType,
    severity: EmergencySeverity
) -> Optional[EmergencyProtocol]:
    """Get appropriate emergency protocol based on type and severity."""
    result = await db.execute(
        select(EmergencyProtocol).where(
            and_(
                EmergencyProtocol.emergency_type == emergency_type,
                EmergencyProtocol.severity == severity,
                EmergencyProtocol.is_active == True
            )
        )
    )
    return result.scalars().first()

async def process_emergency_request(
    db: AsyncSession,
    request: EmergencyResponseCreate
) -> EmergencyResponse:
    """Process emergency request and coordinate response with enhanced location services."""
    try:
        # 1. Create emergency response record
        response = await create_emergency_response(db, request)
        
        # 2. Get appropriate protocol
        protocol = await get_appropriate_protocol(db, request.emergency_type, request.severity)
        
        # 3. Find nearby resources with enhanced location services
        resources = await get_nearby_resources(db, request.location_lat, request.location_lon)
        
        # 4. Get Google Maps data
        # Get route information for each resource
        routes = []
        for resource in resources:
            route = await maps_service.get_route(
                (request.location_lat, request.location_lon),
                (resource.location_lat, resource.location_lon)
            )
            if route:
                routes.append({
                    "resource_id": resource.id,
                    "route": route,
                    "estimated_duration": route["legs"][0]["duration"]["value"],
                    "distance": route["legs"][0]["distance"]["value"]
                })
        
        # Sort resources by estimated arrival time
        routes.sort(key=lambda x: x["estimated_duration"])
        
        # Get traffic conditions
        traffic_conditions = None
        if routes:
            traffic_conditions = {
                "current_traffic": "moderate",  # This would come from Google Maps API
                "traffic_delay": routes[0]["route"]["legs"][0]["duration_in_traffic"]["value"] - 
                               routes[0]["route"]["legs"][0]["duration"]["value"] if "duration_in_traffic" in routes[0]["route"]["legs"][0] else 0
            }
        
        # Get distance matrix for all resources
        distance_matrix = None
        if resources:
            origins = [(request.location_lat, request.location_lon)]
            destinations = [(r.location_lat, r.location_lon) for r in resources]
            matrix = await maps_service.get_distance_matrix(origins, destinations)
            if matrix:
                distance_matrix = {
                    "origins": origins,
                    "destinations": destinations,
                    "distances": matrix[0]["elements"] if matrix else []
                }
        
        # 5. Calculate estimated response time based on Google Maps data
        estimated_time = routes[0]["estimated_duration"] / 60 if routes else 30  # Convert to minutes
        
        # 6. Generate immediate actions
        immediate_actions = generate_immediate_actions(
            request.emergency_type,
            request.severity,
            protocol
        )
        
        # 7. Create follow-up plan
        follow_up_plan = create_follow_up_plan(
            request.emergency_type,
            request.severity,
            protocol
        )
        
        # Store additional information in the response object
        response.actions_taken = immediate_actions
        response.resources_used = [r.id for r in resources] if resources else []
        response.follow_up_notes = str(follow_up_plan)
        response.estimated_response_time = estimated_time
        response.route_information = routes[0] if routes else None
        response.traffic_conditions = traffic_conditions
        response.distance_matrix = distance_matrix
        response.optimized_route = {
            "route": routes[0]["route"] if routes else None,
            "resource_id": routes[0]["resource_id"] if routes else None,
            "estimated_arrival": routes[0]["estimated_duration"] if routes else None
        }
        
        # Update the response in the database
        await db.commit()
        await db.refresh(response)
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing emergency request: {str(e)}")
        raise

def calculate_estimated_response_time(resources: List[EmergencyResource]) -> int:
    """Calculate estimated response time based on available resources."""
    if not resources:
        return 30  # Default fallback time
    
    times = [r.response_time for r in resources if r.response_time]
    return min(times) if times else 30

def generate_immediate_actions(
    emergency_type: EmergencyType,
    severity: EmergencySeverity,
    protocol: Optional[EmergencyProtocol]
) -> List[str]:
    """Generate list of immediate actions based on emergency type and protocol."""
    actions = []
    
    if protocol and protocol.steps:
        actions.extend(protocol.steps)
    else:
        # Default actions based on emergency type
        if emergency_type == EmergencyType.MEDICAL:
            actions.extend([
                "Assess the situation and ensure scene safety",
                "Check for responsiveness and breathing",
                "Call emergency medical services",
                "Begin basic life support if needed"
            ])
        elif emergency_type == EmergencyType.MENTAL_HEALTH:
            actions.extend([
                "Ensure immediate safety",
                "Contact mental health crisis line",
                "Stay with the person",
                "Remove any potential means of self-harm"
            ])
        # Add more default actions for other emergency types
    
    return actions

def create_follow_up_plan(
    emergency_type: EmergencyType,
    severity: EmergencySeverity,
    protocol: Optional[EmergencyProtocol]
) -> Dict:
    """Create follow-up plan based on emergency type and severity."""
    plan = {
        "required_follow_up": severity in [EmergencySeverity.HIGH, EmergencySeverity.CRITICAL],
        "follow_up_timeline": "24 hours" if severity == EmergencySeverity.CRITICAL else "48 hours",
        "recommended_actions": []
    }
    
    if protocol and protocol.success_criteria:
        plan["success_criteria"] = protocol.success_criteria
    
    # Add type-specific follow-up actions
    if emergency_type == EmergencyType.MEDICAL:
        plan["recommended_actions"].extend([
            "Schedule medical follow-up appointment",
            "Review and update emergency contacts",
            "Update medical history if needed"
        ])
    elif emergency_type == EmergencyType.MENTAL_HEALTH:
        plan["recommended_actions"].extend([
            "Schedule mental health assessment",
            "Connect with support groups",
            "Review crisis prevention plan"
        ])
    
    return plan

async def create_emergency_resource(
    db: AsyncSession,
    resource_data: EmergencyResourceCreate
) -> EmergencyResource:
    """Create a new emergency resource."""
    resource = EmergencyResource(**resource_data.dict())
    db.add(resource)
    await db.commit()
    await db.refresh(resource)
    return resource

async def create_emergency_protocol(
    db: AsyncSession,
    protocol_data: EmergencyProtocolCreate
) -> EmergencyProtocol:
    """Create a new emergency protocol."""
    protocol = EmergencyProtocol(**protocol_data.dict())
    db.add(protocol)
    await db.commit()
    await db.refresh(protocol)
    return protocol

async def create_emergency_training(
    db: AsyncSession,
    training_data: EmergencyTrainingCreate
) -> EmergencyTraining:
    """Create a new emergency training record."""
    training = EmergencyTraining(**training_data.dict())
    db.add(training)
    await db.commit()
    await db.refresh(training)
    return training 