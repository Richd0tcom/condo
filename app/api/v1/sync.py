from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any


from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.sync import SyncConfiguration
from app.models.user import User
from app.schemas.sync import SyncConfigurationCreate, SyncConfigurationResponse, SyncResultResponse, SyncTriggerRequest
from app.services.sync_engine import DataSyncEngine, SyncDirection, SyncFrequency, ConflictStrategy
from app.tasks.sync import trigger_sync_task, batch_sync_task


router = APIRouter()



@router.post("/configurations", response_model=SyncConfigurationResponse)
async def create_sync_configuration(
    config_data: SyncConfigurationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new synchronization configuration"""
    
    if not current_user.organization_id:
        raise HTTPException(status_code=400, detail="User must belong to an organization")
    
    sync_engine = DataSyncEngine()
    
    try:
        config = await sync_engine.create_sync_configuration(
            db=db,
            organization_id=str(current_user.organization_id),
            service_name=config_data.service_name,
            entity_type=config_data.entity_type,
            direction=config_data.direction,
            frequency=config_data.frequency,
            conflict_strategy=config_data.conflict_strategy,
            field_mappings=config_data.field_mappings,
            filters=config_data.filters
        )
        
        return SyncConfigurationResponse(
            id=str(config.id),
            service_name=config.service_name,
            entity_type=config.entity_type,
            direction=config.direction,
            frequency=config.frequency,
            conflict_strategy=config.conflict)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/configurations", response_model=List[SyncConfigurationResponse])
async def list_sync_configurations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all sync configurations for the current user's organization"""
    if not current_user.organization_id:
        raise HTTPException(status_code=400, detail="User must belong to an organization")
    

    configs = await db.execute(select(SyncConfiguration).where(SyncConfiguration.organization_id == current_user.organization_id))
    configs = configs.scalars().all()
    result = []
    for config in configs:
        result.append(SyncConfigurationResponse(
            id=str(config.id),
            service_name=config.service_name,
            entity_type=config.entity_type,
            direction=config.direction,
            frequency=config.frequency,
            conflict_strategy=config.conflict_strategy,
            field_mappings=config.field_mappings,
            filters=config.filters,
            is_active=config.is_active,
            last_sync_at=str(config.last_sync_at) if config.last_sync_at else None,
            created_at=str(config.created_at)
        ))
    return result

@router.post("/trigger", response_model=SyncResultResponse)
async def trigger_sync(
    request: SyncTriggerRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Trigger a sync for a service/entity. Runs in background if long-running."""
    if not current_user.organization_id:
        raise HTTPException(status_code=400, detail="User must belong to an organization")
    
    try:
        
        background_tasks.add_task(
            trigger_sync_task.delay,
            str(current_user.organization_id),
            request.service_name,
            request.entity_type,
            request.force
        )
        return SyncResultResponse(
            success=True,
            records_processed=0,
            records_synced=0,
            records_failed=0,
            conflicts_detected=0,
            conflicts_resolved=0,
            errors=[],
            execution_time=0.0
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status", response_model=List[Dict[str, Any]])
async def get_sync_status(
    service_name: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get sync status for the organization (optionally filter by service)."""
    if not current_user.organization_id:
        raise HTTPException(status_code=400, detail="User must belong to an organization")
    
    sync_engine = DataSyncEngine()
    return await sync_engine.get_sync_status(
        db=db,
        organization_id=str(current_user.organization_id),
        service_name=service_name
    )

@router.post("/batch", response_model=Dict[str, SyncResultResponse])
async def batch_sync(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Trigger batch sync for all services in the organization (background)."""
    if not current_user.organization_id:
        raise HTTPException(status_code=400, detail="User must belong to an organization")
    try:
       
        background_tasks.add_task(
            batch_sync_task.delay,
            str(current_user.organization_id)
        )
        return {}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))