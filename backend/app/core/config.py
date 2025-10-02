from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://app:app_password@localhost:5432/anti_phishing"
    
    # JWT
    JWT_SECRET: str = "your-secret-key-change-in-production"
    JWT_REFRESH_SECRET: str = "your-refresh-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Storage
    STORAGE_DRIVER: str = "local"  # local, s3, gcs
    STORAGE_BUCKET: Optional[str] = None
    STORAGE_REGION: Optional[str] = None
    
    # AWS S3 (if using S3)
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    
    # Google Cloud (if using GCS)
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None
    
    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8080"]
    
    # Rate limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 900  # 15 minutes
    
    # File upload
    MAX_FILE_SIZE_MB: int = 20
    ALLOWED_MIME_TYPES: list[str] = [
        "image/png", "image/jpeg", "image/webp",
        "application/pdf",
        "message/rfc822",
        "audio/mpeg", "audio/mp4"
    ]
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    class Config:
        env_file = ".env"


settings = Settings()
