from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from db import get_db
from models.offers import OfferORM

from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

router = APIRouter()

class OfferIn(BaseModel):
    name: str
    url: str
    affiliate_network_id: Optional[int] = None
    countries: Optional[List[Dict[str, Any]]] = []
    payout: Optional[float] = 0
    currency: Optional[str] = "USD"
    status: Optional[str] = "active"
    tokens: Optional[Dict[str, Any]] = {}
    notes: Optional[str] = ''
    tags: Optional[List[str]] = []

class OfferOut(OfferIn):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


@router.get("/", response_model=List[OfferOut])
def get_offers(db: Session = Depends(get_db)):
    return db.query(OfferORM).order_by(OfferORM.id.desc()).all()

@router.post("/")
def create_offer(offer: OfferIn, db: Session = Depends(get_db)):
    new_offer = OfferORM(**offer.dict())
    db.add(new_offer)
    try:
        db.commit()
        db.refresh(new_offer)
        return {"message": "Offer created", "id": new_offer.id}
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Offer with this name already exists")

@router.patch("/{offer_id}")
def update_offer(offer_id: int, offer: OfferIn, db: Session = Depends(get_db)):
    db_offer = db.query(OfferORM).filter_by(id=offer_id).first()
    if not db_offer:
        raise HTTPException(status_code=404, detail="Offer not found")

    for key, value in offer.dict().items():
        setattr(db_offer, key, value)

    db.commit()
    return {"message": "Offer updated"}

@router.delete("/{offer_id}")
def delete_offer(offer_id: int, db: Session = Depends(get_db)):
    db_offer = db.query(OfferORM).filter_by(id=offer_id).first()
    if not db_offer:
        raise HTTPException(status_code=404, detail="Offer not found")

    db.delete(db_offer)
    db.commit()
    return {"message": "Offer deleted"}
