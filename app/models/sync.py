from sqlalchemy import Column, String, DateTime, Boolean, Integer, JSON, Text, Float
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
import uuid

from app.models.base import BaseModel

class SyncConfiguration(BaseModel):
    __tablename__ = "sync_configurations"
    
    organization_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    service_name = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(100), nullable=False)
    direction = Column(String(20), nullable=False)  # inbound, outbound, bidirectional
    frequency = Column(String(20), nullable=False)  # real_time, every_5_min, hourly, daily
    conflict_strategy = Column(String(50), nullable=False)
    field_mappings = Column(JSON, nullable=False)
    filters = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    last_sync_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)

class SyncStatus(BaseModel):
    __tablename__ = "sync_status"
    
    organization_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    service_name = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False)  # running, completed, failed, paused
    progress_percentage = Column(Integer, default=0)
    records_processed = Column(Integer, default=0)
    records_remaining = Column(Integer, default=0)
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

class DataSyncLog(BaseModel):
    __tablename__ = "data_sync_logs"
    
    organization_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    service_name = Column(String(100), nullable=False, index=True)
    status = Column(String(20), nullable=False)
    records_processed = Column(Integer, default=0)
    records_synced = Column(Integer, default=0)
    records_failed = Column(Integer, default=0)
    conflicts_detected = Column(Integer, default=0)
    conflicts_resolved = Column(Integer, default=0)
    execution_time = Column(Float, default=0.0)
    errors = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False)

class ConflictResolution(BaseModel):
    __tablename__ = "conflict_resolutions"
    
    organization_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    service_name = Column(String(100), nullable=False)
    entity_type = Column(String(100), nullable=False)
    internal_id = Column(String(255), nullable=True)
    external_id = Column(String(255), nullable=False)
    internal_data = Column(JSON, nullable=False)
    external_data = Column(JSON, nullable=False)
    status = Column(String(20), default="pending")  # pending, resolved, ignored
    resolution_strategy = Column(String(50), nullable=True)
    resolved_by = Column(UUID(as_uuid=True), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False)