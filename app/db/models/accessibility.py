from sqlalchemy import Column, Integer, String, Boolean, JSON, ForeignKey, DateTime, Text,UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base

class UserAccessibility(Base):
    """
    Stores user accessibility preferences and requirements.
    """
    __tablename__ = "user_accessibility"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    preferred_language = Column(String(10), nullable=False, default="en")
    language_variant = Column(String(10), nullable=True)  # e.g., zh-CN, hi-IN, ar-SA
    voice_enabled = Column(Boolean, default=True)
    voice_language = Column(String(10), nullable=True)
    voice_speed = Column(Integer, default=1)  # 1-5
    text_size = Column(Integer, default=2)  # 1-5
    high_contrast = Column(Boolean, default=False)
    screen_reader = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="accessibility_preferences")

class ContentTranslation(Base):
    """
    Stores translations for UI content and resources.
    """
    __tablename__ = "content_translations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    original_text = Column(Text, nullable=False)
    translated_text = Column(Text, nullable=False)
    source_language = Column(String(10), nullable=False)
    target_language = Column(String(10), nullable=False)
    language_variant = Column(String(10), nullable=True)  # e.g., zh-CN, hi-IN, ar-SA
    medical_terms = Column(JSON, nullable=True)  # Store medical term mappings
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="translations")

class VoiceCommand(Base):
    __tablename__ = "voice_commands"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    command = Column(Text, nullable=False)
    intent = Column(String(50), nullable=False)  # navigation, action, query
    parameters = Column(JSON, nullable=True)
    confidence = Column(Integer, nullable=True)  # 0-100
    success = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="voice_commands")

class MedicalTerm(Base):
    __tablename__ = "medical_terms"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(50), nullable=False)  # medications, allergies, conditions
    language_code = Column(String(10), nullable=False)
    language_variant = Column(String(10), nullable=True)  # e.g., zh-CN, hi-IN, ar-SA
    term = Column(Text, nullable=False)
    translation = Column(Text, nullable=False)
    transliteration = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Indexes
    __table_args__ = (
        # Ensure unique terms per language variant
        UniqueConstraint('category', 'language_code', 'language_variant', 'term', name='uix_medical_term'),
    )

class AccessibilityLog(Base):
    """
    Tracks accessibility feature usage and issues.
    """
    __tablename__ = "accessibility_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    feature_used = Column(String(50), nullable=False)  # translation, voice_command, etc.
    success = Column(Boolean, default=True)
    meta_data = Column(JSON, nullable=True)  # Additional context about the usage
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="accessibility_logs") 