from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List
from db import get_db
from models.base import Base

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime

router = APIRouter()

class Conversion(Base):
    __tablename__ = "conversions_data"

    id = Column(Integer, primary_key=True, index=True)
    received_at = Column(DateTime)
    click_id = Column(String)
    campaign_id = Column(Integer)
    offer_id = Column(Integer)
    landing_id = Column(Integer)
    status = Column(String)
    external_id = Column(String)
    payout = Column(Float)
    revenue = Column(Float)
    profit = Column(Float)
    currency = Column(String)
    transaction_id = Column(String)
    country = Column(String)
    region = Column(String)
    city = Column(String)
    ip = Column(String)
    visitor_id = Column(String)
    sub_id_1 = Column(String)
    sub_id_2 = Column(String)
    sub_id_3 = Column(String)
    sub_id_4 = Column(String)
    sub_id_5 = Column(String)
    sub_id_6 = Column(String)
    sub_id_7 = Column(String)
    sub_id_8 = Column(String)
    sub_id_9 = Column(String)
    sub_id_10 = Column(String)
    utm_campaign = Column(String)
    utm_creative = Column(String)
    utm_source = Column(String)
    traffic_source_name = Column(String)
    os = Column(String)
    isp = Column(String)
    is_using_proxy = Column(Boolean)
    is_bot = Column(Boolean)
    device_type = Column(String)

@router.get("/")
def get_conversions(request: Request, limit: int = 100, db: Session = Depends(get_db)):

    # разрешённые поля фильтрации
    ALLOWED_FILTER_FIELDS = {
        "campaign_id", "offer_id", "landing_id", "status", "click_id", "external_id",
        "sub_id_1", "sub_id_2", "sub_id_3", "sub_id_4", "sub_id_5",
        "sub_id_6", "sub_id_7", "sub_id_8", "sub_id_9", "sub_id_10",
        "utm_source", "utm_campaign", "utm_creative", "traffic_source_name"
    }

    query = db.query(Conversion)

    # Применяем фильтры
    for key, value in request.query_params.items():
        if key in ALLOWED_FILTER_FIELDS:
            column = getattr(Conversion, key, None)
            if column is not None:
                query = query.filter(column == value)
        elif key == "date_from":
            query = query.filter(Conversion.received_at >= datetime.fromisoformat(value))
        elif key == "date_to":
            query = query.filter(Conversion.received_at <= datetime.fromisoformat(value))

    rows = query.order_by(Conversion.received_at.desc()).limit(limit).all()

    # Преобразуем ORM-объекты в dict
    return [row.__dict__ for row in rows]
