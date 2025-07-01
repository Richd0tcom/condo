from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from fastapi import Depends, Request
import logging
from .settings import settings

logger = logging.getLogger(__name__)
print("---------LOADED SETTINGS------",settings.DATABASE_URL )

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
        if tenant_id:
            db.execute(f"SET app.current_tenant = '{tenant_id}'")
        yield db
    except Exception as e:
        logger.error(f"Tenant DB session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()