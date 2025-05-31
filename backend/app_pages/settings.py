from fastapi import APIRouter, Depends, HTTPException
import json
from sqlalchemy.orm import Session
from sqlalchemy import text
from db import get_db
from models.settings import SettingsORM  # модель settings

router = APIRouter()


from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

router = APIRouter()

@router.post("/clear-tracking-data")
async def clear_tracking_data(
    request: Request,
    db: Session = Depends(get_db)
):

    try:
        ch = request.app.state.ch
        ch.command("TRUNCATE TABLE clicks_data")
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"ClickHouse error: {str(e)}"})

    try:
        db.execute(text("TRUNCATE TABLE conversions_data RESTART IDENTITY CASCADE"))
        db.commit()
    except Exception as e:
        db.rollback()
        return JSONResponse(status_code=500, content={"error": f"PostgreSQL error: {str(e)}"})

    return {"status": "ok", "message": "Tracking data cleared from ClickHouse and PostgreSQL"}



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
