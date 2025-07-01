from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
import asyncio
import json
import logging
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import hashlib

from app.core.database import get_db
from app.models.sync import SyncConfiguration, SyncStatus, DataSyncLog, ConflictResolution
from app.models.organization import Organization
from app.integrations.external_client import ExternalApiClient

logger = logging.getLogger(__name__)

class SyncDirection(str, Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound" 
    BIDIRECTIONAL = "bidirectional"

class ConflictStrategy(str, Enum):
    EXTERNAL_WINS = "external_wins"
    INTERNAL_WINS = "internal_wins"
    LATEST_TIMESTAMP = "latest_timestamp"
    MANUAL_REVIEW = "manual_review"

class SyncFrequency(str, Enum):
    REAL_TIME = "real_time"
    EVERY_5_MIN = "every_5_min"
    HOURLY = "hourly"
    DAILY = "daily"

@dataclass
class SyncResult:
    success: bool
    records_processed: int
    records_synced: int
    records_failed: int
    conflicts_detected: int
    conflicts_resolved: int
    errors: List[str]
    execution_time: float

@dataclass
class DataRecord:
    external_id: str
    internal_id: Optional[str]
    data: Dict[str, Any]
    last_modified: datetime
    checksum: str
    source: str

class DataSyncEngine:
    """
    Comprehensive data synchronization engine for multi-tenant SaaS platform
    Handles bidirectional sync, conflict resolution, and batch operations
    """
    
    def __init__(self):
        self.external_client = ExternalApiClient()
        self.sync_locks = {}  


    async def create_sync_configuration(
        self, 
        db: AsyncSession,
        organization_id: str,
        service_name: str,
        entity_type: str,
        direction: SyncDirection,
        frequency: SyncFrequency,
        conflict_strategy: ConflictStrategy,
        field_mappings: Dict[str, str],
        filters: Optional[Dict[str, Any]] = None
    ) -> SyncConfiguration:
        """Create a new sync configuration for an organization"""
        
        config = SyncConfiguration(
            organization_id=organization_id,
            service_name=service_name,
            entity_type=entity_type,
            direction=direction,
            frequency=frequency,
            conflict_strategy=conflict_strategy,
            field_mappings=field_mappings,
            filters=filters or {},
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        db.add(config)
        await db.commit()
        await db.refresh(config)
        
        logger.info(f"Created sync config for org {organization_id}, service {service_name}")
        return config
    
    async def trigger_sync(
        self,
        db: AsyncSession,
        organization_id: str,
        service_name: str,
        entity_type: Optional[str] = None,
        force: bool = False
    ) -> SyncResult:
        """Trigger synchronization for specified organization and service"""
        
        lock_key = f"sync_lock:{organization_id}:{service_name}"
        
        if lock_key in self.sync_locks and not force:
            raise ValueError("Sync already in progress for this service")
            
        try:
            self.sync_locks[lock_key] = True
            
            query = select(SyncConfiguration).where(
                and_(
                    SyncConfiguration.organization_id == organization_id,
                    SyncConfiguration.service_name == service_name,
                    SyncConfiguration.is_active == True
                )
            )
            
            if entity_type:
                query = query.where(SyncConfiguration.entity_type == entity_type)
                
            result = await db.execute(query)
            configs = result.scalars().all()
            
            if not configs:
                return SyncResult(
                    success=False,
                    records_processed=0,
                    records_synced=0,
                    records_failed=0,
                    conflicts_detected=0,
                    conflicts_resolved=0,
                    errors=["No active sync configurations found"],
                    execution_time=0.0
                )
            
            start_time = datetime.utcnow()
            total_result = SyncResult(
                success=True,
                records_processed=0,
                records_synced=0,
                records_failed=0,
                conflicts_detected=0,
                conflicts_resolved=0,
                errors=[],
                execution_time=0.0
            )
            
            for config in configs:
                try:
                    result = await self._execute_sync(db, config)
                    
                    total_result.records_processed += result.records_processed
                    total_result.records_synced += result.records_synced
                    total_result.records_failed += result.records_failed
                    total_result.conflicts_detected += result.conflicts_detected
                    total_result.conflicts_resolved += result.conflicts_resolved
                    total_result.errors.extend(result.errors)
                    
                    if not result.success:
                        total_result.success = False
                        
                except Exception as e:
                    logger.error(f"Sync failed for config {config.id}: {str(e)}")
                    total_result.success = False
                    total_result.errors.append(f"Config {config.id}: {str(e)}")
            
            end_time = datetime.utcnow()
            total_result.execution_time = (end_time - start_time).total_seconds()
            
            await self._log_sync_execution(db, organization_id, service_name, total_result)
            
            return total_result
            
        finally:
            self.sync_locks.pop(lock_key, None)
    
    async def _execute_sync(
        self,
        db: AsyncSession,
        config: SyncConfiguration
    ) -> SyncResult:
        """Execute synchronization for a specific configuration"""
        
        result = SyncResult(
            success=True,
            records_processed=0,
            records_synced=0,
            records_failed=0,
            conflicts_detected=0,
            conflicts_resolved=0,
            errors=[],
            execution_time=0.0
        )
        
        start_time = datetime.utcnow()
        
        try:
            if config.direction in [SyncDirection.INBOUND, SyncDirection.BIDIRECTIONAL]:
                inbound_result = await self._sync_inbound(db, config)
                self._merge_results(result, inbound_result)
            
            if config.direction in [SyncDirection.OUTBOUND, SyncDirection.BIDIRECTIONAL]:
                outbound_result = await self._sync_outbound(db, config)
                self._merge_results(result, outbound_result)
                
        except Exception as e:
            logger.error(f"Sync execution failed for config {config.id}: {str(e)}")
            result.success = False
            result.errors.append(str(e))
        
        end_time = datetime.utcnow()
        result.execution_time = (end_time - start_time).total_seconds()
        
        return result
    
    async def _sync_inbound(
        self,
        db: AsyncSession,
        config: SyncConfiguration
    ) -> SyncResult:
        """Sync data from external service to internal database"""
        
        result = SyncResult(
            success=True,
            records_processed=0,
            records_synced=0,
            records_failed=0,
            conflicts_detected=0,
            conflicts_resolved=0,
            errors=[],
            execution_time=0.0
        )
        
        try:
            external_records = await self._fetch_external_data(config)
            result.records_processed = len(external_records)
            
            for external_record in external_records:
                try:
                    sync_success = await self._sync_record_inbound(
                        db, config, external_record
                    )
                    
                    if sync_success:
                        result.records_synced += 1
                    else:
                        result.records_failed += 1
                        
                except Exception as e:
                    logger.error(f"Failed to sync record {external_record.external_id}: {str(e)}")
                    result.records_failed += 1
                    result.errors.append(f"Record {external_record.external_id}: {str(e)}")
            
        except Exception as e:
            logger.error(f"Inbound sync failed for config {config.id}: {str(e)}")
            result.success = False
            result.errors.append(str(e))
        
        return result
    
    async def _sync_outbound(
        self,
        db: AsyncSession,
        config: SyncConfiguration
    ) -> SyncResult:
        """Sync data from internal database to external service"""
        
        result = SyncResult(
            success=True,
            records_processed=0,
            records_synced=0,
            records_failed=0,
            conflicts_detected=0,
            conflicts_resolved=0,
            errors=[],
            execution_time=0.0
        )
        
        try:
            # Fetch internal data that needs syncing
            internal_records = await self._fetch_internal_data(db, config)
            result.records_processed = len(internal_records)
            
            for internal_record in internal_records:
                try:
                    sync_success = await self._sync_record_outbound(
                        db, config, internal_record
                    )
                    
                    if sync_success:
                        result.records_synced += 1
                    else:
                        result.records_failed += 1
                        
                except Exception as e:
                    logger.error(f"Failed to sync record {internal_record.internal_id}: {str(e)}")
                    result.records_failed += 1
                    result.errors.append(f"Record {internal_record.internal_id}: {str(e)}")
            
        except Exception as e:
            logger.error(f"Outbound sync failed for config {config.id}: {str(e)}")
            result.success = False
            result.errors.append(str(e))
        
        return result
    
    async def _sync_record_inbound(
        self,
        db: AsyncSession,
        config: SyncConfiguration,
        external_record: DataRecord
    ) -> bool:
        """Sync a single record from external service to internal database"""
        
        try:
            # Check if record already exists internally
            internal_record = await self._find_internal_record(
                db, config, external_record.external_id
            )
            
            if internal_record:
                
                conflict_detected = await self._detect_conflict(
                    config, internal_record, external_record
                )
                
                if conflict_detected:
                    resolution = await self._resolve_conflict(
                        db, config, internal_record, external_record
                    )
                    
                    if resolution == "skip":
                        return True  
                    elif resolution == "external_wins":
                        await self._update_internal_record(
                            db, config, internal_record, external_record
                        )
                    # If internal_wins, do nothing
                else:
                    # No conflict, update if external is newer
                    if external_record.last_modified > internal_record.last_modified:
                        await self._update_internal_record(
                            db, config, internal_record, external_record
                        )
            else:
                # Create new internal record
                await self._create_internal_record(
                    db, config, external_record
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to sync inbound record: {str(e)}")
            return False
    
    async def _sync_record_outbound(
        self,
        db: AsyncSession,
        config: SyncConfiguration,
        internal_record: DataRecord
    ) -> bool:
        """Sync a single record from internal database to external service"""
        
        try:
            # Check if record exists in external service
            external_record = await self._find_external_record(
                config, internal_record.internal_id
            )
            
            if external_record:
                conflict_detected = await self._detect_conflict(
                    config, internal_record, external_record
                )
                
                if conflict_detected:
                    resolution = await self._resolve_conflict(
                        db, config, internal_record, external_record
                    )
                    
                    if resolution == "skip":
                        return True
                    elif resolution == "internal_wins":
                        await self._update_external_record(
                            config, external_record, internal_record
                        )
                else:
                    # No conflict, update if internal is newer
                    if internal_record.last_modified > external_record.last_modified:
                        await self._update_external_record(
                            config, external_record, internal_record
                        )
            else:
                # Create new external record
                await self._create_external_record(
                    config, internal_record
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to sync outbound record: {str(e)}")
            return False
    
    async def _detect_conflict(
        self,
        config: SyncConfiguration,
        record1: DataRecord,
        record2: DataRecord
    ) -> bool:
        """Detect if there's a conflict between two records"""
        
        # Compare checksums
        if record1.checksum != record2.checksum:
            # Check if both records were modified recently
            time_threshold = timedelta(minutes=10)
            now = datetime.utcnow()
            
            record1_recent = (now - record1.last_modified) < time_threshold
            record2_recent = (now - record2.last_modified) < time_threshold
            
            return record1_recent and record2_recent
        
        return False
    
    async def _resolve_conflict(
        self,
        db: AsyncSession,
        config: SyncConfiguration,
        internal_record: DataRecord,
        external_record: DataRecord
    ) -> str:
        """Resolve conflict between internal and external records"""
        
        if config.conflict_strategy == ConflictStrategy.EXTERNAL_WINS:
            return "external_wins"
        elif config.conflict_strategy == ConflictStrategy.INTERNAL_WINS:
            return "internal_wins"
        elif config.conflict_strategy == ConflictStrategy.LATEST_TIMESTAMP:
            if external_record.last_modified > internal_record.last_modified:
                return "external_wins"
            else:
                return "internal_wins"
        elif config.conflict_strategy == ConflictStrategy.MANUAL_REVIEW:
            # Log conflict for manual review
            await self._log_conflict(
                db, config, internal_record, external_record
            )
            return "skip"
        
        return "skip"
    
    async def batch_sync(
        self,
        db: AsyncSession,
        organization_id: str,
        batch_size: int = 100
    ) -> Dict[str, SyncResult]:
        """Perform batch synchronization for all services of an organization"""
        
        results = {}
        
        # Get all active sync configurations for the organization
        query = select(SyncConfiguration).where(
            and_(
                SyncConfiguration.organization_id == organization_id,
                SyncConfiguration.is_active == True
            )
        )
        
        result = await db.execute(query)
        configs = result.scalars().all()
        
        
        service_configs = {}
        for config in configs:
            if config.service_name not in service_configs:
                service_configs[config.service_name] = []
            service_configs[config.service_name].append(config)
        
        # Process each service
        for service_name, configs in service_configs.items():
            try:
                result = await self.trigger_sync(
                    db, organization_id, service_name
                )
                results[service_name] = result
                
            except Exception as e:
                logger.error(f"Batch sync failed for service {service_name}: {str(e)}")
                results[service_name] = SyncResult(
                    success=False,
                    records_processed=0,
                    records_synced=0,
                    records_failed=0,
                    conflicts_detected=0,
                    conflicts_resolved=0,
                    errors=[str(e)],
                    execution_time=0.0
                )
        
        return results
    
    async def get_sync_status(
        self,
        db: AsyncSession,
        organization_id: str,
        service_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get synchronization status for organization services"""
        
        query = select(SyncConfiguration).where(
            SyncConfiguration.organization_id == organization_id
        )
        
        if service_name:
            query = query.where(SyncConfiguration.service_name == service_name)
        
        result = await db.execute(query)
        configs = result.scalars().all()
        
        status_list = []
        
        for config in configs:
            
            log_query = select(DataSyncLog).where(
                and_(
                    DataSyncLog.organization_id == organization_id,
                    DataSyncLog.service_name == config.service_name
                )
            ).order_by(DataSyncLog.created_at.desc()).limit(1)
            
            log_result = await db.execute(log_query)
            latest_log = log_result.scalar_one_or_none()
            
            status = {
                "config_id": config.id,
                "service_name": config.service_name,
                "entity_type": config.entity_type,
                "direction": config.direction,
                "frequency": config.frequency,
                "is_active": config.is_active,
                "last_sync": latest_log.created_at if latest_log else None,
                "last_sync_status": latest_log.status if latest_log else None,
                "records_synced": latest_log.records_synced if latest_log else 0,
                "conflicts_detected": latest_log.conflicts_detected if latest_log else 0,
                "next_sync": self._calculate_next_sync(config)
            }
            
            status_list.append(status)
        
        return status_list
    
    def _calculate_checksum(self, data: Dict[str, Any]) -> str:
        """Calculate checksum for data integrity verification"""
        
        
        sorted_data = json.dumps(data, sort_keys=True, default=str)
        return hashlib.md5(sorted_data.encode()).hexdigest()
    
    def _calculate_next_sync(self, config: SyncConfiguration) -> Optional[datetime]:
        """Calculate next sync time based on frequency"""
        
        if not config.last_sync_at:
            return datetime.utcnow()
        
        if config.frequency == SyncFrequency.REAL_TIME:
            return None  
        elif config.frequency == SyncFrequency.EVERY_5_MIN:
            return config.last_sync_at + timedelta(minutes=5)
        elif config.frequency == SyncFrequency.HOURLY:
            return config.last_sync_at + timedelta(hours=1)
        elif config.frequency == SyncFrequency.DAILY:
            return config.last_sync_at + timedelta(days=1)
        
        return None
    
    def _merge_results(self, target: SyncResult, source: SyncResult):
        """Merge sync results"""
        
        target.records_processed += source.records_processed
        target.records_synced += source.records_synced
        target.records_failed += source.records_failed
        target.conflicts_detected += source.conflicts_detected
        target.conflicts_resolved += source.conflicts_resolved
        target.errors.extend(source.errors)
        
        if not source.success:
            target.success = False
    
    
    async def _fetch_external_data(self, config: SyncConfiguration) -> List[DataRecord]:
        """Fetch data from external service"""
       
        return []
    
    async def _fetch_internal_data(self, db: AsyncSession, config: SyncConfiguration) -> List[DataRecord]:
        """Fetch internal data that needs syncing"""
        
        return []
    
    async def _find_internal_record(self, db: AsyncSession, config: SyncConfiguration, external_id: str) -> Optional[DataRecord]:
        """Find internal record by external ID"""
       
        return None
    
    async def _find_external_record(self, config: SyncConfiguration, internal_id: str) -> Optional[DataRecord]:
        """Find external record by internal ID"""
        
        return None
    
    async def _create_internal_record(self, db: AsyncSession, config: SyncConfiguration, external_record: DataRecord):
        """Create new internal record from external data"""
        pass
    
    async def _update_internal_record(self, db: AsyncSession, config: SyncConfiguration, internal_record: DataRecord, external_record: DataRecord):
        """Update internal record with external data"""
        pass
    
    async def _create_external_record(self, config: SyncConfiguration, internal_record: DataRecord):
        """Create new external record from internal data"""
        pass
    
    async def _update_external_record(self, config: SyncConfiguration, external_record: DataRecord, internal_record: DataRecord):
        """Update external record with internal data"""
        pass
    
    async def _log_sync_execution(self, db: AsyncSession, organization_id: str, service_name: str, result: SyncResult):
        """Log sync execution results"""
        
        log_entry = DataSyncLog(
            organization_id=organization_id,
            service_name=service_name,
            status="success" if result.success else "failed",
            records_processed=result.records_processed,
            records_synced=result.records_synced,
            records_failed=result.records_failed,
            conflicts_detected=result.conflicts_detected,
            conflicts_resolved=result.conflicts_resolved,
            execution_time=result.execution_time,
            errors=result.errors,
            created_at=datetime.utcnow()
        )
        
        db.add(log_entry)
        await db.commit()
    
    async def _log_conflict(self, db: AsyncSession, config: SyncConfiguration, internal_record: DataRecord, external_record: DataRecord):
        """Log conflict for manual review"""
        
        conflict = ConflictResolution(
            organization_id=config.organization_id,
            service_name=config.service_name,
            entity_type=config.entity_type,
            internal_id=internal_record.internal_id,
            external_id=external_record.external_id,
            internal_data=internal_record.data,
            external_data=external_record.data,
            status="pending",
            created_at=datetime.utcnow()
        )
        
        db.add(conflict)
        await db.commit()