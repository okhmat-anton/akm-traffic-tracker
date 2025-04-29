from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class SettingsORM(Base):
    __tablename__ = "settings"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    value = Column(String, nullable=False)
