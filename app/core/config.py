from pydantic_settings import BaseSettings
import base64
from cryptography.fernet import Fernet
from typing import Optional

class Settings(BaseSettings):
    # General Application Config
    APP_NAME: str = "Health Management Assistant"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "dummy-secret-key-for-development"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  
    FRONTEND_URL: str = "http://localhost:3000"

    # Database Config
    DB_HOST: str = "localhost"
    DB_PORT: str = "5432"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "seven"
    DB_NAME: str = "project_db_new"

    # Security Config
    ALGORITHM: str = "HS256"
    TOKEN_URL: str = "/api/v1/auth/token"  

    # Encryption Config
    ENCRYPTION_KEY: str = Fernet.generate_key().decode()
    MESSAGE_RETENTION_DAYS: int = 365
    ENCRYPTION_ALGORITHM: str = "AES-256-GCM"
    #FERNET_KEY: str = base64.urlsafe_b64encode(b"dummy-fernet-key-for-development-32-bytes-long").decode()
    
    # AI Services
    OPENAI_API_KEY: str = "dummy-openai-key"
    
    STRIPE_SECRET_KEY: str = "dummy-stripe-key"
    STRIPE_WEBHOOK_SECRET: str = "dummy-webhook-secret"
    
    ELEVENLABS_API_KEY: str = "dummy-elevenlabs-key"
    AHPRA_PIE_API_KEY: str = "dummy-ahpra-key"
    
    # Google Services
    GOOGLE_MAPS_API_KEY: str = "dummy-google-maps-key"
    GOOGLE_CLIENT_ID: str = "dummy-google-client-id"
    GOOGLE_CLIENT_SECRET: str = "dummy-google-client-secret"
    GOOGLE_OAUTH_REDIRECT_URI: str = "http://localhost:8000/api/v1/wearables/google/callback"

    # Fitbit OAuth
    FITBIT_CLIENT_ID: str = "dummy-fitbit-client-id"
    FITBIT_CLIENT_SECRET: str = "dummy-fitbit-client-secret"
    FITBIT_REDIRECT_URI: str = "http://localhost:8000/auth/fitbit/callback"
    
    # Email & SMS
    EMAIL_HOST: str = "smtp.gmail.com"
    EMAIL_PORT: int = 587
    EMAIL_USERNAME: str = "dummy@email.com"
    EMAIL_PASSWORD: str = "dummy-password"
    SMS_API_KEY: str = "dummy-sms-key"

    # Insurance Provider API Settings
    INSURANCE_PROVIDER_API_KEY: str
    INSURANCE_PROVIDER_API_URL: str = "https://api.insurance-provider.com/v1"

    # JWT Settings for Digital Wallet
    JWT_PRIVATE_KEY_PATH: str = "keys/private.pem"
    JWT_PUBLIC_KEY_PATH: str = "keys/public.pem"
    JWT_PRIVATE_KEY_PASSWORD: Optional[str] = None
    JWT_KEY_ID: str
     
    EMERGENCY_API_URL: str = "https://api.emergency-service.com/v1"
    EMERGENCY_API_KEY: str = "dummy-emergency-key"
    # Apple Wallet Settings
    APPLE_TEAM_ID: str
    APPLE_PASS_TYPE_ID: str
    ORGANIZATION_NAME: str = "Health Management Assistant"

    # Verification Settings
    VERIFICATION_BASE_URL: str = "https://verify.health-management.com"

    # Construct SQLAlchemy Database URL properly
    @property
    def SQLALCHEMY_DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    class Config:
        case_sensitive = True
        env_file = ".env" 
        env_file_encoding = "utf-8"      

settings = Settings()
