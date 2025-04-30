from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db import get_db
from models.campaigns import CampaignORM
from typing import List

from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime

router = APIRouter()

class CampaignIn(BaseModel):
    name: str
    type: Literal['campaign', 'tracking-only'] = 'campaign'
    status: Literal['active', 'paused', 'archived'] = 'active'
    redirect_mode: Literal['random', 'sequential', 'weight', 'single'] = 'random'
    traffic_source_id: Optional[int] = None
    domain_id: Optional[int] = None
    notes: Optional[str] = None

class CampaignOut(CampaignIn):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


@router.get("/", response_model=List[CampaignOut])
def get_campaigns(db: Session = Depends(get_db)):
    return db.query(CampaignORM).order_by(CampaignORM.id.asc()).all()

@router.post("/", response_model=dict)
def create_campaign(data: CampaignIn, db: Session = Depends(get_db)):
    campaign = CampaignORM(**data.dict())
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return {"message": "Campaign created", "id": campaign.id}

@router.patch("/{campaign_id}")
def update_campaign(campaign_id: int, data: CampaignIn, db: Session = Depends(get_db)):
    campaign = db.query(CampaignORM).filter_by(id=campaign_id).first()
    if not campaign:
        raise HTTPException(404, detail="Campaign not found")

    for key, value in data.dict().items():
        setattr(campaign, key, value)

    db.commit()
    return {"message": "Campaign updated"}

@router.delete("/{campaign_id}")
def delete_campaign(campaign_id: int, db: Session = Depends(get_db)):
    campaign = db.query(CampaignORM).filter_by(id=campaign_id).first()
    if not campaign:
        raise HTTPException(404, detail="Campaign not found")

    db.delete(campaign)
    db.commit()
    return {"message": "Campaign deleted"}
