from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from db import get_db
from models.sources import SourceORM

from pydantic import BaseModel
from typing import Optional, List, Dict, Any

router = APIRouter()


class SourceIn(BaseModel):
    name: str
    traffic_loss: Optional[float] = 0
    s2s_postback: Optional[str] = None
    s2s_postback_statuses: Optional[Dict[str, bool]] = {}
    settings: List[Dict[str, Any]] = []
    additional_settings: Dict[str, Any] = {}


class SourceOut(SourceIn):
    id: int
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True


@router.get("/", response_model=List[SourceOut])
def get_sources(db: Session = Depends(get_db)):
    return db.query(SourceORM).order_by(SourceORM.id.asc()).all()


@router.post("/", response_model=SourceOut)
def create_source(payload: SourceIn, db: Session = Depends(get_db)):
    source = SourceORM(**payload.dict())
    db.add(source)
    try:
        db.commit()
        db.refresh(source)
        return source
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Source with this name already exists.")


@router.patch("/{source_id}", response_model=SourceOut)
def update_source(source_id: int, payload: SourceIn, db: Session = Depends(get_db)):
    source = db.query(SourceORM).filter(SourceORM.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    for key, value in payload.dict(exclude_unset=True).items():
        setattr(source, key, value)

    db.commit()
    db.refresh(source)
    return source


@router.delete("/{source_id}")
def delete_source(source_id: int, db: Session = Depends(get_db)):
    source = db.query(SourceORM).filter(SourceORM.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    db.delete(source)
    db.commit()
    return {"message": "Source deleted"}
