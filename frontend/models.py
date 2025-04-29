from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Landing(Base):
    __tablename__ = "landings"

    id = Column(Integer, primary_key=True, index=True)
    folder = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    tags = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
