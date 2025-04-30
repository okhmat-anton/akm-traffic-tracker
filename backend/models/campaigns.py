from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.sql import func
from models.base import Base

campaign_type_enum = ENUM('campaign', 'tracking-only', name='campaign_type', create_type=False)
campaign_status_enum = ENUM('active', 'paused', 'archived', name='campaign_status', create_type=False)
redirect_mode_enum = ENUM('random', 'sequential', 'weight', 'single', name='redirect_mode', create_type=False)

class CampaignORM(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    type = Column(campaign_type_enum, default='campaign')
    status = Column(campaign_status_enum, default='active')
    redirect_mode = Column(redirect_mode_enum, default='random')
    traffic_source_id = Column(Integer, ForeignKey("sources.id", ondelete="SET NULL"))
    domain_id = Column(Integer, ForeignKey("domains.id", ondelete="SET NULL"))
    notes = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
