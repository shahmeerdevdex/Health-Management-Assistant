from sqlalchemy import Column, Integer, String, Float, JSON, ForeignKey, DateTime, Enum, Boolean, Text, Table
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.db.base import Base

class EmergencyType(str, enum.Enum):
    MEDICAL = "medical"
    MENTAL_HEALTH = "mental_health"
    TRAUMA = "trauma"
    CARDIAC = "cardiac"
    RESPIRATORY = "respiratory"
    NEUROLOGICAL = "neurological"
    PEDIATRIC = "pediatric"
    OBSTETRICAL = "obstetrical"
    PSYCHIATRIC = "psychiatric"
    OTHER = "other"

class EmergencySeverity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class EmergencyStatus(str, enum.Enum):
    INITIALIZED = "initialized"
    DISPATCHED = "dispatched"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CANCELLED = "cancelled"

class EmergencyResponse(Base):
    """
    Stores emergency response records and actions taken.
    """
    __tablename__ = "emergency_responses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    emergency_type = Column(Enum(EmergencyType), nullable=False)
    severity = Column(Enum(EmergencySeverity), nullable=False)
    location_lat = Column(Float, nullable=True)
    location_lon = Column(Float, nullable=True)
    description = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=False), nullable=False, default=datetime.now)
    dispatched_at = Column(DateTime(timezone=False), nullable=True)
    resolved_at = Column(DateTime(timezone=False), nullable=True)
    status = Column(Enum(EmergencyStatus), nullable=False, default=EmergencyStatus.INITIALIZED)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)  # Emergency responder ID
    actions_taken = Column(JSON, nullable=False, default=list)  # List of actions taken
    resources_used = Column(JSON, nullable=True)  # Emergency resources utilized
    follow_up_required = Column(Boolean, default=True)
    follow_up_notes = Column(Text, nullable=True)
    updated_at = Column(DateTime(timezone=False), default=datetime.now, onupdate=datetime.now)
    
    # New fields for Google Maps integration
    estimated_response_time = Column(Integer, nullable=True)  # Estimated response time in minutes
    route_information = Column(JSON, nullable=True)  # Detailed route information from Google Maps
    geocoded_address = Column(String, nullable=True)  # Human-readable address from coordinates
    traffic_conditions = Column(JSON, nullable=True)  # Current traffic conditions
    distance_matrix = Column(JSON, nullable=True)  # Distance matrix for nearby resources
    optimized_route = Column(JSON, nullable=True)  # Optimized route for response

    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="emergency_responses")
    responder = relationship("User", foreign_keys=[assigned_to])
    dispatches = relationship("EmergencyDispatch", back_populates="emergency")
    tracking = relationship("EmergencyTracking", back_populates="emergency", uselist=False)
    resources = relationship("EmergencyResource", back_populates="current_emergency")
    
class EmergencyResource(Base):
    """
    Stores emergency resources and their availability.
    """
    __tablename__ = "emergency_resources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # ambulance, police, fire, mental_health, etc.
    contact = Column(String, nullable=False)
    location_lat = Column(Float, nullable=True)
    location_lon = Column(Float, nullable=True)
    availability = Column(Boolean, default=True)
    capacity = Column(Integer, nullable=True)
    current_usage = Column(Integer, default=0)
    response_time = Column(Integer, nullable=True)  # Average response time in minutes
    coverage_area = Column(JSON, nullable=True)  # Geographic coverage area
    specializations = Column(JSON, nullable=True)  # Special capabilities
    last_updated = Column(DateTime(timezone=False), nullable=False, default=datetime.now, onupdate=datetime.now)
    capability_score = Column(Float, default=1.0)
    assigned_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    current_emergency_id = Column(Integer, ForeignKey("emergency_responses.id"), nullable=True)
    created_at = Column(DateTime(timezone=False), default=datetime.now)
    updated_at = Column(DateTime(timezone=False), default=datetime.now, onupdate=datetime.now)

    # Relationships
    user = relationship("User", foreign_keys=[assigned_user_id], back_populates="assigned_resources")
    current_emergency = relationship("EmergencyResponse", back_populates="resources")
    dispatches = relationship("EmergencyDispatch", back_populates="resource")
    inventory = relationship("EmergencyResourceInventory", back_populates="resource", cascade="all, delete-orphan")


class EmergencyTeam(Base):
    __tablename__ = "emergency_teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    type = Column(String)  # medical, fire, police, etc.
    leader_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String, default="available")
    created_at = Column(DateTime(timezone=False), default=datetime.now)
    updated_at = Column(DateTime(timezone=False), default=datetime.now, onupdate=datetime.now)

    # Relationships
    leader = relationship("User", back_populates="led_teams")
    members = relationship("User", secondary="team_members", back_populates="teams")

class EmergencyZone(Base):
    __tablename__ = "emergency_zones"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    center_lat = Column(Float)
    center_lon = Column(Float)
    radius_km = Column(Float)
    type = Column(String)  # hospital, school, residential, etc.
    active_emergencies = Column(Integer, default=0)
    protocol = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=False), default=datetime.now)
    updated_at = Column(DateTime(timezone=False), default=datetime.now, onupdate=datetime.now)

class EmergencyDispatch(Base):
    __tablename__ = "emergency_dispatches"

    id = Column(Integer, primary_key=True, index=True)
    emergency_id = Column(Integer, ForeignKey("emergency_responses.id"))
    resource_id = Column(Integer, ForeignKey("emergency_resources.id"))
    status = Column(String)  # dispatched, arrived, completed, cancelled
    dispatch_time = Column(DateTime(timezone=False), default=datetime.now)
    arrival_time = Column(DateTime(timezone=False), nullable=True)
    completion_time = Column(DateTime(timezone=False), nullable=True)
    notes = Column(String, nullable=True)

    # Relationships
    emergency = relationship("EmergencyResponse", back_populates="dispatches")
    resource = relationship("EmergencyResource", back_populates="dispatches")

class EmergencyTracking(Base):
    __tablename__ = "emergency_tracking"

    id = Column(Integer, primary_key=True, index=True)
    emergency_id = Column(Integer, ForeignKey("emergency_responses.id"))
    status = Column(String)
    location_lat = Column(Float)
    location_lon = Column(Float)
    last_updated = Column(DateTime(timezone=False), default=datetime.now)
    meta_data = Column(JSON, nullable=True)

    # Relationships
    emergency = relationship("EmergencyResponse", back_populates="tracking")

class EmergencyResourceInventory(Base):
    __tablename__ = "emergency_resource_inventory"

    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(Integer, ForeignKey("emergency_resources.id"))
    item_type = Column(String)
    quantity = Column(Integer)
    last_restocked = Column(DateTime(timezone=False), default=datetime.now)
    minimum_quantity = Column(Integer)
    maximum_quantity = Column(Integer)
    notes = Column(String, nullable=True)

    # Relationships
    resource = relationship("EmergencyResource", back_populates="inventory")

# Association table for team members
team_members = Table(
    "team_members",
    Base.metadata,
    Column("team_id", Integer, ForeignKey("emergency_teams.id")),
    Column("user_id", Integer, ForeignKey("users.id"))
)

class EmergencyProtocol(Base):
    """
    Stores emergency response protocols and procedures.
    """
    __tablename__ = "emergency_protocols"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    emergency_type = Column(Enum(EmergencyType), nullable=False)
    severity = Column(Enum(EmergencySeverity), nullable=False)
    steps = Column(JSON, nullable=False)  # Ordered list of steps to follow
    required_resources = Column(JSON, nullable=True)  # Required resources for this protocol
    estimated_duration = Column(Integer, nullable=True)  # Estimated duration in minutes
    success_criteria = Column(JSON, nullable=True)  # Criteria for successful resolution
    last_reviewed = Column(DateTime(timezone=False), nullable=False, default=datetime.now)
    is_active = Column(Boolean, default=True)

class EmergencyTraining(Base):
    """
    Stores emergency response training records.
    """
    __tablename__ = "emergency_training"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    training_type = Column(String, nullable=False)  # CPR, First Aid, Crisis Intervention, etc.
    certification_id = Column(String, nullable=True)
    issue_date = Column(DateTime(timezone=False), nullable=False)
    expiry_date = Column(DateTime(timezone=False), nullable=True)
    provider = Column(String, nullable=False)
    status = Column(String, nullable=False)  # active, expired, pending
    verification_document = Column(String, nullable=True)  # URL to verification document
    notes = Column(Text, nullable=True)

    # Relationships
    user = relationship("User", back_populates="emergency_training") 