# models/user.py

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    username = Column(String(255), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=True)
    password_hash = Column(Text, nullable=False)
    is_admin = Column(Boolean, server_default="false", nullable=False)
    active = Column(Boolean, server_default="true", nullable=False)

    def __repr__(self):
        return f"<User(username='{self.username}', email='{self.email}')>"
