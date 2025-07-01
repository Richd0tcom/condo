from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from app.services.sync_engine import ConflictStrategy, SyncDirection, SyncFrequency


class SyncConfigurationCreate(BaseModel):
    service_name: str
    entity_type: str
    direction: SyncDirection
    frequency: SyncFrequency
    conflict_strategy: ConflictStrategy
    field_mappings: Dict[str, str]
    filters: Optional[Dict[str, Any]] = None

class SyncConfigurationResponse(BaseModel):
    id: str
    service_name: str
    entity_type: str
    direction: str
    frequency: str
    conflict_strategy: str
    field_mappings: Dict[str, str]
    filters: Optional[Dict[str, Any]]
    is_active: bool
    last_sync_at: Optional[str]
    created_at: str

class SyncTriggerRequest(BaseModel):
    service_name: str
    entity_type: Optional[str] = None
    force: bool = False

class SyncResultResponse(BaseModel):
    success: bool
    records_processed: int
    records_synced: int
    records_failed: int
    conflicts_detected: int
    conflicts_resolved: int
    errors: List[str]
    execution_time: float