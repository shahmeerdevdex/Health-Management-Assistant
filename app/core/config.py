from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # General Application Config
    APP_NAME: str = "Health Management Assistant"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  

    # Database Config
    DB_HOST: str
    DB_PORT: str
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str

    # Security Config
    ALGORITHM: str = "HS256"
    TOKEN_URL: str = "/api/v1/auth/token"  

    # AI Services
    OPENAI_API_KEY: str
    
    STRIPE_SECRET_KEY:str
    
    STRIPE_WEBHOOK_SECRET:str
    
    ELEVENLABS_API_KEY:str
    
    
      # Google Fit OAuth
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_OAUTH_REDIRECT_URI: str

    # Fitbit OAuth
    FITBIT_CLIENT_ID: str
    FITBIT_CLIENT_SECRET: str
    FITBIT_REDIRECT_URI: str
    
    
    # Email & SMS
    EMAIL_HOST: str
    EMAIL_PORT: int
    EMAIL_USERNAME: str
    EMAIL_PASSWORD: str
    SMS_API_KEY: str

    # Construct SQLAlchemy Database URL properly
    @property
    def SQLALCHEMY_DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    class Config:
        case_sensitive = True
        env_file = ".env" 
        env_file_encoding = "utf-8"      


settings = Settings()
