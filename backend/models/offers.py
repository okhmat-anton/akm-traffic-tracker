from sqlalchemy import Column, Integer, String, Text, Numeric, TIMESTAMP, func, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from models.base import Base

class OfferORM(Base):
    __tablename__ = "offers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    url = Column(Text, nullable=False)
    affiliate_network_id = Column(Integer, ForeignKey("affiliate_networks.id", ondelete="SET NULL"))
    countries = Column(JSONB)
    payout = Column(Numeric(10, 2))
    currency = Column(String(10), default="USD")
    status = Column(String(20), default="active")
    tokens = Column(JSONB)
    notes = Column(Text)
    tags = Column(ARRAY(String))
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
