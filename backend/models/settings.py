from sqlalchemy import Column, Integer, String
from models.base import Base

class SettingsORM(Base):
    __tablename__ = "settings"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    value = Column(String, nullable=False)
