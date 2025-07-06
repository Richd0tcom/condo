from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict # type: ignore
from typing import List, Optional
import secrets

class Settings(BaseSettings):
    PROJECT_NAME: str = "Orion"
    VERSION: str = "1"
    API_V1_STR: str = "/api/v1"
    
    
    DATABASE_URL: str
    
    
    REDIS_URL: str = "redis://localhost:6379/0"

    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    WEBHOOK_SIGNATURE_TOLERANCE_SECONDS: int = 300
    INTEGRATION_HEALTH_CHECK_INTERVAL: int = 60
    MAX_WEBHOOK_PAYLOAD_SIZE: int = 1024*1024  # 1MB

    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 5
    CIRCUIT_BREAKER_RECOVERY_TIMEOUT: int = 60

    # Rate Limiting
    DEFAULT_RATE_LIMIT_PER_SECOND: float = 10.0
    BURST_RATE_LIMIT_PER_SECOND: float = 100.0
    
    
    JWT_SECRET_KEY: str = secrets.token_urlsafe(32)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    
    RATE_LIMIT_PER_MINUTE: int = 60
    
    
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    EXTERNAL_USER_SERVICE_URL: str = "http://localhost:8001"
    EXTERNAL_PAYMENT_SERVICE_URL: str = "http://localhost:8002"
    EXTERNAL_COMMS_SERVICE_URL: str = "http://localhost:8003"
    
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

settings = Settings()