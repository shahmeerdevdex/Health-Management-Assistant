from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(String, nullable=False)  # Encrypted content
    timestamp = Column(DateTime, default=datetime.utcnow)
    is_read = Column(Boolean, default=False)
    
    # New fields for HIPAA/GDPR compliance
    message_type = Column(String, nullable=False, default="general")  # general, medical, sensitive
    retention_period = Column(Integer, nullable=False, default=365)  # Days to retain message
    audit_log = Column(JSON, nullable=True)  # Track message access and modifications
    is_encrypted = Column(Boolean, default=True)
    deleted_at = Column(DateTime, nullable=True)
    message_metadata = Column(JSON, nullable=True)  # Renamed from metadata to message_metadata

    # Relationships
    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_messages")
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="received_messages")

class MessageAuditLog(Base):
    __tablename__ = "message_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String, nullable=False)  # read, delete, modify, etc.
    timestamp = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    additional_info = Column(JSON, nullable=True)

    # Relationships
    message = relationship("Message", backref="audit_logs")
    user = relationship("User", backref="message_audit_logs")
