import logging
import sys
from logging.handlers import RotatingFileHandler

# Define log format
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
LOG_LEVEL = logging.INFO  # Change to DEBUG for more details

# Create a logger
logger = logging.getLogger("health_management_assistant")
logger.setLevel(LOG_LEVEL)

# Console logging
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
logger.addHandler(console_handler)

# File logging with rotation (max 5MB per file, keeps last 3 logs)
file_handler = RotatingFileHandler("logs/app.log", maxBytes=5 * 1024 * 1024, backupCount=3)
file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
logger.addHandler(file_handler)

# Separate logs for security-related events
security_handler = RotatingFileHandler("logs/security.log", maxBytes=2 * 1024 * 1024, backupCount=2)
security_handler.setFormatter(logging.Formatter(LOG_FORMAT))
security_handler.setLevel(logging.WARNING)  # Capture only WARNING and ERROR logs
logger.addHandler(security_handler)

# AI and Insights logs
ai_handler = RotatingFileHandler("logs/ai.log", maxBytes=3 * 1024 * 1024, backupCount=2)
ai_handler.setFormatter(logging.Formatter(LOG_FORMAT))
logger.addHandler(ai_handler)

# API request logs
api_handler = RotatingFileHandler("logs/api.log", maxBytes=5 * 1024 * 1024, backupCount=3)
api_handler.setFormatter(logging.Formatter(LOG_FORMAT))
logger.addHandler(api_handler)

# Optional: Integrate with Sentry or External Logging Service
# try:
#     import sentry_sdk
#     from sentry_sdk.integrations.logging import LoggingIntegration

#     sentry_sdk.init(
#         dsn="your_sentry_dsn",  
#         integrations=[LoggingIntegration(level=logging.ERROR, event_level=logging.ERROR)],
#     )
# except ImportError:
#     logger.warning("Sentry SDK not installed. Install it with `pip install sentry-sdk` if needed.")

# Logging Categories
def log_security(message):
    logger.warning(f"SECURITY: {message}")

def log_api_request(message):
    logger.info(f"API_REQUEST: {message}")

def log_ai_activity(message):
    logger.info(f"AI_ACTIVITY: {message}")

def log_error(message):
    logger.error(f"ERROR: {message}")

logger.info("Logging setup complete.")
