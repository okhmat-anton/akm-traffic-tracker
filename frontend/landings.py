from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional
import zipfile, os, shutil
from datetime import datetime

from db import get_db
from models import Landing

router = APIRouter()

LANDINGS_DIR = "/app/landings"  # путь внутри контейнера src
os.makedirs(LANDINGS_DIR, exist_ok=True)


def get_next_site_id():
    existing = [f for f in os.listdir(LANDINGS_DIR) if
                f.startswith("site_") and os.path.isdir(os.path.join(LANDINGS_DIR, f))]
    numbers = [int(f.replace("site_", "")) for f in existing if f.replace("site_", "").isdigit()]
    return max(numbers, default=0) + 1


@router.post("/landing")
async def upload_landing(
        file: UploadFile = File(...),
        name: str = Form(...),
        site_folder: str = Form(...),
        tags: str = Form(...),
        db: Session = Depends(get_db)
):
    site_id = get_next_site_id()
    if site_folder is None or site_folder == "":
        site_folder = f"site_{site_id}"
    full_path = os.path.join(LANDINGS_DIR, site_folder)
    os.makedirs(full_path, exist_ok=True)

    temp_zip = os.path.join(full_path, "temp.zip")
    with open(temp_zip, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
            zip_ref.extractall(full_path)
    except Exception as e:
        shutil.rmtree(full_path)
        raise HTTPException(status_code=400, detail=f"Failed to unzip: {e}")
    finally:
        os.remove(temp_zip)

    landing = Landing(
        folder=site_folder,
        name=name,
        tags=tags,
        created_at=datetime.utcnow()
    )
    db.add(landing)
    db.commit()
    db.refresh(landing)

    return {
        "status": "ok",
        "site": site_folder,
        "url": f"/landing/{site_folder}/",
        "id": landing.id
    }



def landing_path(folder):
    return os.path.join(LANDINGS_DIR, folder)

def save_zip(file: UploadFile, folder_path: str):
    temp_zip = os.path.join(folder_path, "temp.zip")
    with open(temp_zip, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
            zip_ref.extractall(folder_path)
    finally:
        os.remove(temp_zip)


@router.get("/landing/{landing_id}")
def get_landing(landing_id: int, db: Session = Depends(get_db)):
    landing = db.query(Landing).filter(Landing.id == landing_id).first()
    if not landing:
        raise HTTPException(status_code=404, detail="Landing not found")
    return {
        "id": landing.id,
        "folder": landing.folder,
        "name": landing.name,
        "tags": landing.tags.split(",") if landing.tags else [],
        "created_at": landing.created_at
    }

@router.put("/landing/{landing_id}")
async def update_landing(
    landing_id: int,
    name: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    landing = db.query(Landing).filter(Landing.id == landing_id).first()
    if not landing:
        raise HTTPException(status_code=404, detail="Landing not found")

    if name:
        landing.name = name
    if tags:
        landing.tags = tags

    folder_path = landing_path(landing.folder)

    if file:
        # Очистка папки перед загрузкой нового файла
        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)
            if os.path.isfile(item_path):
                os.remove(item_path)
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)

        save_zip(file, folder_path)

    db.commit()
    db.refresh(landing)

    return {"status": "updated", "id": landing.id}

@router.delete("/landing/{landing_id}")
def delete_landing(landing_id: int, db: Session = Depends(get_db)):
    landing = db.query(Landing).filter(Landing.id == landing_id).first()
    if not landing:
        raise HTTPException(status_code=404, detail="Landing not found")

    # Удаляем папку
    folder_path = landing_path(landing.folder)
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)

    # Удаляем запись в базе
    db.delete(landing)
    db.commit()

    return {"status": "deleted", "id": landing_id}