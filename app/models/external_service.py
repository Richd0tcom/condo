from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import JSONB
from app.models.base import BaseModel

class ExternalService(BaseModel):
    __tablename__ = 'external_services'

    slug = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    webhook_url = Column(String, nullable=False)
    api_base_url = Column(String, nullable=False)
    auth_type = Column(String, nullable=False)
    secret_key = Column(String, nullable=False)
    retry_policy = Column(JSONB)
    event_types = Column(JSONB)
    rate_limit = Column(JSONB)
