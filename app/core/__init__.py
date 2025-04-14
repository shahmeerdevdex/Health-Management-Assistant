from app.core.config import settings
from app.core.security import hash_password, verify_password
from app.core.logging_config import logger
from app.core.scheduler import celery
from app.services.ai_services import analyze_symptoms, get_personalized_health_tips, detect_health_patterns

# Expose key configurations and services
__all__ = [
    "settings",
    "hash_password",
    "verify_password",
    "logger",
    "celery",
    "analyze_symptoms",
    "get_personalized_health_tips",
    "detect_health_patterns"
]

logger.info("Core modules initialized.")
