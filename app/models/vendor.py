from sqlalchemy import UUID, Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Vendor(BaseModel):
    __tablename__ = 'vendors'

    name = Column(String, unique=True, index=True, nullable=False)
    
    events = relationship("VendorEvent", back_populates="vendor")


class VendorEvent(BaseModel):
    __tablename__ = 'vendor_events'

    name = Column(String, index=True, nullable=False)
    vendor_id = Column(UUID(as_uuid=True), ForeignKey('vendors.id', ondelete="CASCADE"))
    
    vendor = relationship("Vendor", back_populates="events")
