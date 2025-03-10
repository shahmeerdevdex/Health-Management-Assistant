from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    # General Application Config
    APP_NAME: str = "Health Management Assistant"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  

    # Database Config
    DB_HOST : str = os.getenv("DB_HOST")
    DB_PORT: str = os.getenv("DB_PORT")
    DB_USER: str = os.getenv("DB_USER")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD")
    DB_NAME: str = os.getenv("DB_NAME")

    # Construct SQLAlchemy Database URL properly
    @property
    def SQLALCHEMY_DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # Security Config
    ALGORITHM: str = "HS256"
    TOKEN_URL: str = "/auth/token"

    # AI Services
    OPENAI_API_KEY: str

    # Email & SMS
    EMAIL_HOST: str
    EMAIL_PORT: int
    EMAIL_USERNAME: str
    EMAIL_PASSWORD: str
    SMS_API_KEY: str

    class Config:
        case_sensitive = True
        env_file = ".env"  
        env_file_encoding = 'utf-8'  # Optional: Ensures proper encoding



# ✅ Create a settings instance
settings = Settings()
