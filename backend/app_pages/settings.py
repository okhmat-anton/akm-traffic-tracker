from fastapi import APIRouter, Depends, HTTPException
import json
from sqlalchemy.orm import Session
from db import get_db
from models.settings import SettingsORM  # модель settings

router = APIRouter()

@router.get("/")
def get_settings(db: Session = Depends(get_db)):
    rows = db.query(SettingsORM).all()
    out = {}
    for row in rows:
        try:
            out[row.name] = json.loads(row.value)
        except Exception:
            out[row.name] = row.value
    return out

@router.post("/")
def save_settings(payload: dict, db: Session = Depends(get_db)):
    for key, val in payload.items():
        val_str = json.dumps(val)
        setting = db.query(SettingsORM).filter_by(name=key).first()
        if setting:
            setting.value = val_str
        else:
            setting = SettingsORM(name=key, value=val_str)
            db.add(setting)
    db.commit()
    return {"status": "ok"}
