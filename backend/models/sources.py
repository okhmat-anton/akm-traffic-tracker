# models/sources.py

from sqlalchemy import Column, Integer, String, Float, Text, JSON, TIMESTAMP, func
from models.base import Base

class SourceORM(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    traffic_loss = Column(Float, default=0)
    s2s_postback = Column(String(1024), nullable=True)
    s2s_postback_statuses = Column(JSON, default={})

    settings = Column(JSON, default=[])
    additional_settings = Column(JSON, default={})

    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
