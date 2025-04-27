# models/domain.py

from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class DomainModel(Base):
    __tablename__ = "domains"

    id = Column(Integer, primary_key=True, index=True)
    domain = Column(String(255), unique=True, nullable=False)
    redirect_https = Column(Boolean, nullable=False, server_default="true")
    handle_404 = Column(String(50), nullable=False, server_default="error")
    default_company = Column(String(255), nullable=True)
    group_name = Column(String(255), nullable=True)
    status = Column(String(50), nullable=False, server_default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Domain(domain='{self.domain}', status='{self.status}')>"
