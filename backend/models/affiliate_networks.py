from sqlalchemy import Column, Integer, String, TIMESTAMP, func
from models.base import Base

class AffiliateNetworkORM(Base):
    __tablename__ = "affiliate_networks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    offer_parameters = Column(String(1024))
    s2s_postback = Column(String(1024))
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
