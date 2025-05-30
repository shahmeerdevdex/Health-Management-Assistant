from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base
from app.schemas.digital_wallet import CredentialType, CredentialStatus

class DigitalCredential(Base):
    __tablename__ = "digital_credentials"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    credential_type = Column(SQLEnum(CredentialType), nullable=False)
    credential_data = Column(JSON, nullable=False)
    status = Column(SQLEnum(CredentialStatus), nullable=False, default=CredentialStatus.PENDING)
    issued_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    issuer = Column(String, nullable=False)
    verification_status = Column(Boolean, default=False)
    verification_timestamp = Column(DateTime, nullable=True)
    credential_metadata = Column(JSON, nullable=True)

    # Relationships
    user = relationship("User", back_populates="digital_credentials")
    shares = relationship("CredentialShare", back_populates="credential")

class CredentialShare(Base):
    __tablename__ = "credential_shares"

    id = Column(Integer, primary_key=True, index=True)
    credential_id = Column(Integer, ForeignKey("digital_credentials.id"), nullable=False)
    recipient_email = Column(String, nullable=False)
    recipient_name = Column(String, nullable=False)
    access_duration = Column(Integer, nullable=True)  # Duration in hours
    purpose = Column(String, nullable=False)
    scope = Column(JSON, nullable=False)  # List of allowed actions
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

    # Relationships
    credential = relationship("DigitalCredential", back_populates="shares")

class CredentialVerification(Base):
    __tablename__ = "credential_verifications"

    id = Column(Integer, primary_key=True, index=True)
    credential_id = Column(Integer, ForeignKey("digital_credentials.id"), nullable=False)
    verification_method = Column(String, nullable=False)
    verification_data = Column(JSON, nullable=False)
    verification_result = Column(Boolean, nullable=False)
    verification_timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    verification_metadata = Column(JSON, nullable=True)

    # Relationships
    credential = relationship("DigitalCredential") 