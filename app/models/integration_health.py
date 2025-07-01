from sqlalchemy import Column, Integer, String, DateTime, Float, Text
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB

from app.models.base import BaseModel

class IntegrationHealth(BaseModel):
    """Model for monitoring integration health"""
    __tablename__ = "integration_health"
    
    
    service_name = Column(String(100), nullable=False, index=True)
    status = Column(String(50), nullable=False)
    response_time_ms = Column(Float, nullable=False)
    error_message = Column(Text, nullable=True)
    data = Column(JSONB, default=dict)
    checked_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
