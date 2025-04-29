from sqlalchemy import Column, Integer, String, Enum, DateTime
from sqlalchemy.ext.declarative import declarative_base
import enum

Base = declarative_base()

class LandingMood(enum.Enum):
    link = "link"
    mirror = "mirror"
    local_file = "local_file"

class Landing(Base):
    __tablename__ = "landings"

    id = Column(Integer, primary_key=True, index=True)
    folder = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), unique=True, nullable=False)
    link = Column(String(255), nullable=True)
    type = Column(Enum(LandingMood), nullable=False)
    tags = Column(String(255), nullable=True)
    created_at = Column(DateTime)
