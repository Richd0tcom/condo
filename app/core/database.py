from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from fastapi import Depends, Request
import logging
from .settings import settings

logger = logging.getLogger(__name__)


engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=20,
    max_overflow=0,
    echo=settings.DEBUG
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db() -> Session:
    """Database dependency for FastAPI"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def get_tenant_db(request: Request) -> Session:
    """
    Database dependency that sets the tenant context for RLS.
    Assumes tenant_id is available in request.state.tenant_id.
    """
    db = SessionLocal()
    try:
        tenant_id = getattr(request.state, "tenant_id", None)
        print("tennnnnn from requesterrrrr", tenant_id)
        if tenant_id:
            db.execute(f"SET app.current_tenant = '{tenant_id}'")
        yield db
    except Exception as e:
        logger.error(f"Tenant DB session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def get_org_db(request: Request) -> Session:
    """
    Database dependency that sets the tenant context for RLS.
    Assumes tenant_id is available in request.state.tenant_id.
    """
    db = SessionLocal()
    try:
        org_id = getattr(request.state, "tenant_id", None)
        if org_id:
            db.execute(f"SET app.current_org = '{org_id}'")
        yield db
    except Exception as e:
        logger.error(f"Org DB session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Context manager for database sessions - for manual usage"""
    db = SessionLocal()
    try:
        yield db
        db.commit()  # Auto-commit on success
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

# Alternative: Function that returns a context manager
def db_session():
    """Returns a context manager for database sessions"""
    return get_db_session()

# For async contexts (if you prefer async/await style)
class AsyncDatabaseSession:
    def __init__(self):
        self.db = None
    
    async def __aenter__(self) -> Session:
        self.db = SessionLocal()
        return self.db
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is None:
                self.db.commit()
            else:
                self.db.rollback()
        finally:
            self.db.close()

def get_async_db_session():
    """Get async database session context manager"""
    return AsyncDatabaseSession()