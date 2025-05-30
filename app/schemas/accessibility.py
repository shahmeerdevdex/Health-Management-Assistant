from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


# -------------------- User Accessibility --------------------

class UserAccessibilityBase(BaseModel):
    voice_enabled: bool = Field(True, description="Whether voice features are enabled")
    voice_speed: int = Field(1, ge=1, le=5, description="Voice speed (1-5)")
    text_size: int = Field(2, ge=1, le=5, description="Text size (1-5)")
    high_contrast: bool = Field(False, description="Whether high contrast mode is enabled")
    screen_reader: bool = Field(False, description="Whether screen reader is enabled")


class UserAccessibilityCreate(UserAccessibilityBase):
    user_id: int = Field(..., description="ID of the user")


class UserAccessibilityUpdate(UserAccessibilityBase):
    voice_enabled: Optional[bool] = None
    voice_speed: Optional[int] = None
    text_size: Optional[int] = None
    high_contrast: Optional[bool] = None
    screen_reader: Optional[bool] = None


class UserAccessibilityResponse(UserAccessibilityBase):
    id: int
    user_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


# -------------------- Translation --------------------

class TranslationRequest(BaseModel):
    text: str = Field(..., description="Text to translate")
    source_language: Optional[str] = Field(None, description="Source language code")
    target_language: str = Field(..., description="Target language code")
    context: Optional[str] = Field(None, description="Translation context (e.g., medical)")


class TranslationResponse(BaseModel):
    translated_text: str
    source_language: str
    target_language: str
    is_rtl: bool
    medical_terms: Optional[List[Dict[str, Any]]] = None


# -------------------- Voice Command --------------------

class VoiceCommandRequest(BaseModel):
    """Request model for voice command processing."""
    pass


class VoiceCommandResponse(BaseModel):
    """Response model for voice command processing."""
    original_text: str = Field(..., description="Original transcribed text")
    command_result: Optional[Dict[str, Any]] = Field(None, description="Processed command result")


# -------------------- Medical Term --------------------

class MedicalTermResponse(BaseModel):
    translated: str
    is_medical_term: bool
    category: Optional[str] = None
    transliteration: Optional[str] = None


# -------------------- Language Variant --------------------

class LanguageVariantResponse(BaseModel):
    language_code: str
    variant: str
    available_variants: List[str]


# -------------------- Voice Command History --------------------

class VoiceCommandHistory(BaseModel):
    command: str
    intent: str
    parameters: Optional[Dict[str, Any]] = None
    confidence: Optional[int] = None
    success: bool
    timestamp: datetime

    class Config:
        orm_mode = True


# -------------------- Accessibility Logs --------------------

class AccessibilityLogBase(BaseModel):
    feature_used: str
    success: bool
    meta_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class AccessibilityLogCreate(AccessibilityLogBase):
    user_id: int


class AccessibilityLogResponse(AccessibilityLogBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        orm_mode = True


# -------------------- Content Translation --------------------

class ContentTranslationBase(BaseModel):
    original_text: str
    translated_text: str
    source_language: str
    target_language: str
    language_variant: Optional[str] = None
    medical_terms: Optional[List[Dict[str, Any]]] = None


class ContentTranslationCreate(ContentTranslationBase):
    user_id: int


class ContentTranslationResponse(ContentTranslationBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        orm_mode = True
