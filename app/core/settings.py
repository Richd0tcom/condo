from pydantic_settings import BaseSettings # type: ignore
from typing import List, Optional
import secrets

class Settings(BaseSettings):
    PROJECT_NAME: str = "Orion"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    
    DATABASE_URL: str
    
    
    REDIS_URL: str
    
    
    JWT_SECRET_KEY: str = secrets.token_urlsafe(32)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    
    RATE_LIMIT_PER_MINUTE: int = 60
    
    
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()