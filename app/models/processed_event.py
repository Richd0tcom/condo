from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB

from app.models.base import BaseModel



class ProcessedEvent(BaseModel):
    """Model for tracking processed events for idempotency"""
    __tablename__ = "processed_events"
    
    
    event_hash = Column(String(64), unique=True, nullable=False, index=True)
    event_id = Column(String(255), nullable=False)
    source = Column(String(100), nullable=False)
    event_type = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False, default='pending')
    processed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    data = Column(JSONB, default=dict)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
