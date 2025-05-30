from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Enum, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.schemas.ehr_sync import EHRSystem, NationalDatabaseType
import enum
from datetime import datetime

class EHRConnection(Base):
    __tablename__ = "ehr_connections"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    ehr_system = Column(String, nullable=False)  # e.g., "epic", "cerner", etc.
    access_token = Column(String, nullable=False)
    refresh_token = Column(String)
    token_expires_at = Column(DateTime)
    connection_config = Column(JSON)  # Stores system-specific configuration
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="ehr_connections")
    national_database_connections = relationship("NationalDatabaseConnection", back_populates="ehr_connection")
    records = relationship("EHRRecord", back_populates="connection")

class EHRRecord(Base):
    __tablename__ = "ehr_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    connection_id = Column(Integer, ForeignKey("ehr_connections.id"), nullable=False)
    medical_history = Column(JSON)  # Stores medical history data
    medications = Column(JSON)  # Stores medication data
    procedures = Column(JSON)  # Stores procedure data
    allergies = Column(JSON)  # Stores allergy data
    immunizations = Column(JSON)
    last_synced = Column(DateTime, default=datetime.utcnow)
    sync_status = Column(String)
    sync_message = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="ehr_records")
    connection = relationship("EHRConnection", back_populates="records")
    fhir_resources = relationship("FHIRResourceCache", back_populates="record")

class FHIRResourceCache(Base):
    __tablename__ = "fhir_resource_cache"

    id = Column(Integer, primary_key=True, index=True)
    record_id = Column(Integer, ForeignKey("ehr_records.id"), nullable=False)
    resource_type = Column(String, nullable=False)
    resource_id = Column(String, nullable=False)
    data = Column(JSON, nullable=False)
    version = Column(String, nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow)
    source_system = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    record = relationship("EHRRecord", back_populates="fhir_resources")

class NationalDatabaseConnection(Base):
    __tablename__ = "national_database_connections"

    id = Column(Integer, primary_key=True, index=True)
    ehr_connection_id = Column(Integer, ForeignKey("ehr_connections.id"), nullable=False)
    database_type = Column(String, nullable=False)
    provider_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    encrypted_credentials = Column(JSON, nullable=False)
    credential_hash = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    last_verified = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    ehr_connection = relationship("EHRConnection", back_populates="national_database_connections")
    provider = relationship("User", foreign_keys=[provider_id])
    sync_records = relationship("NationalDatabaseSyncRecord", back_populates="connection")

class NationalDatabaseSyncRecord(Base):
    __tablename__ = "national_database_sync_records"

    id = Column(Integer, primary_key=True, index=True)
    connection_id = Column(Integer, ForeignKey("national_database_connections.id"), nullable=False)
    sync_type = Column(String, nullable=False)  # e.g., "full", "incremental"
    status = Column(String, nullable=False)
    message = Column(String)
    data_synced = Column(JSON)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    connection = relationship("NationalDatabaseConnection", back_populates="sync_records")
