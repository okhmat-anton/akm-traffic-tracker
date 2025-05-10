# models/domain.py

from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from models.base import Base


class DomainORM(Base):
    __tablename__ = "domains"

    id = Column(Integer, primary_key=True, index=True)
    domain = Column(String(255), unique=True, nullable=False)
    redirect_https = Column(Boolean, nullable=False, server_default="true")
    handle_404 = Column(String(50), nullable=False, server_default="error")
    default_campaign_id = Column(Integer, nullable=True)
    group_name = Column(String(255), nullable=True)
    status = Column(String(50), nullable=False, server_default="pending")
    ssl_status = Column(String(50), nullable=False, server_default="not_started")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Domain(domain='{self.domain}', status='{self.status}')>"
