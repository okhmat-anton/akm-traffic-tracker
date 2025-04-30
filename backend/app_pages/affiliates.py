from fastapi import APIRouter, Depends, HTTPException
from typing import List
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from db import get_db
from models.affiliate_networks import AffiliateNetworkORM
from models.offers import OfferORM  # не забудь импортировать

router = APIRouter()


class AffiliateNetworkIn(BaseModel):
    name: str
    offer_parameters: Optional[str] = ''
    s2s_postback: Optional[str] = ''


class AffiliateNetworkOut(AffiliateNetworkIn):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


@router.get("/", response_model=List[AffiliateNetworkOut])
def get_networks(db: Session = Depends(get_db)):
    return db.query(AffiliateNetworkORM).order_by(AffiliateNetworkORM.id.desc()).all()


@router.post("/")
def create_network(data: AffiliateNetworkIn, db: Session = Depends(get_db)):
    new = AffiliateNetworkORM(**data.dict())
    db.add(new)
    try:
        db.commit()
        db.refresh(new)
        return {"message": "Affiliate network created", "id": new.id}
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Affiliate network with this name already exists")


@router.patch("/{network_id}")
def update_network(network_id: int, data: AffiliateNetworkIn, db: Session = Depends(get_db)):
    net = db.query(AffiliateNetworkORM).filter_by(id=network_id).first()
    if not net:
        raise HTTPException(status_code=404, detail="Affiliate network not found")

    for key, value in data.dict().items():
        setattr(net, key, value)

    db.commit()
    return {"message": "Affiliate network updated"}


@router.delete("/{network_id}")
def delete_network(network_id: int, db: Session = Depends(get_db)):
    # Найти сеть
    net = db.query(AffiliateNetworkORM).filter_by(id=network_id).first()
    if not net:
        raise HTTPException(status_code=404, detail="Affiliate network not found")

    # Проверить, есть ли офферы, привязанные к этой сети
    has_offers = db.query(OfferORM).filter_by(affiliate_network_id=network_id).first()
    if has_offers:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete affiliate network with linked offers. Delete offers first!"
        )

    db.delete(net)
    db.commit()
    return {"message": "Affiliate network deleted"}

