from typing import Dict, List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class MockServiceConfig(BaseSettings):
    """Configuration for mock external services"""
    
    # Service URLs
    user_management_url: str = Field("http://localhost:8001", env="USER_MANAGEMENT_URL")
    payment_service_url: str = Field("http://localhost:8002", env="PAYMENT_SERVICE_URL")
    communication_service_url: str = Field("http://localhost:8003", env="COMMUNICATION_SERVICE_URL")
    
    # Webhook secrets
    user_webhook_secret: str = Field("user_webhook_secret_key", env="USER_WEBHOOK_SECRET")
    payment_webhook_secret: str = Field("payment_webhook_secret_key", env="PAYMENT_WEBHOOK_SECRET")
    communication_webhook_secret: str = Field("comm_webhook_secret_key", env="COMMUNICATION_WEBHOOK_SECRET")
    
    # Service discovery
    service_discovery_enabled: bool = Field(True, env="SERVICE_DISCOVERY_ENABLED")
    health_check_interval: int = Field(30, env="HEALTH_CHECK_INTERVAL")  # seconds
    service_timeout: int = Field(30, env="SERVICE_TIMEOUT")  # seconds
    
    # Retry configuration
    max_retries: int = Field(3, env="MAX_RETRIES")
    retry_backoff_factor: float = Field(2.0, env="RETRY_BACKOFF_FACTOR")
    retry_max_delay: int = Field(300, env="RETRY_MAX_DELAY")  # seconds
    
    # Rate limiting
    requests_per_minute: int = Field(1000, env="REQUESTS_PER_MINUTE")
    burst_limit: int = Field(50, env="BURST_LIMIT")
    
    # Event simulation
    event_simulation_enabled: bool = Field(True, env="EVENT_SIMULATION_ENABLED")
    event_generation_interval: int = Field(60, env="EVENT_GENERATION_INTERVAL")  # seconds
    

    model_config = SettingsConfigDict(env_file=".env", env_prefix="MOCK_", extra="ignore")


# Global config instance
mock_service_config = MockServiceConfig()