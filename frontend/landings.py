
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
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

def landing_path(folder):
    return os.path.join(LANDINGS_DIR, folder)


def save_uploaded_file(file: UploadFile, folder_path: str):
    filename = file.filename.lower()

    if filename.endswith('.zip'):
        # Сохраняем и распаковываем архив
        temp_zip = os.path.join(folder_path, "temp.zip")
        with open(temp_zip, "wb") as f:
            shutil.copyfileobj(file.file, f)
        try:
            with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
                zip_ref.extractall(folder_path)
        finally:
            os.remove(temp_zip)

    elif filename.endswith('.php') or filename.endswith('.html'):
        # Сохраняем файл как есть
        os.makedirs(folder_path, exist_ok=True)
        file_path = os.path.join(folder_path, filename)
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type. Only .zip, .php, .html allowed.")

@router.post("/landing")
async def upload_landing(
        name: str = Form(...),
        site_folder: str = Form(...),
        type: int = Form(...),  # теперь int
        tags: str = Form(""),
        link: Optional[str] = Form(None),
        file: Optional[UploadFile] = File(None),
        db: Session = Depends(get_db)
):
    type_mapping = {0: 'link', 1: 'mirror', 2: 'local_file'}
    landing_type = type_mapping.get(type)

    if landing_type is None:
        raise HTTPException(status_code=400, detail="Invalid landing type.")

    # Обработка если файл передан как пустая строка
    if isinstance(file, str) and file == "":
        file = None

    if landing_type in ('link', 'mirror') and not link:
        raise HTTPException(status_code=400, detail="Link is required for 'link' or 'mirror' type.")

    if landing_type == 'local_file' and not file:
        raise HTTPException(status_code=400, detail="File is required for 'local_file' type.")

    site_id = get_next_site_id()
    if not site_folder:
        site_folder = f"site_{site_id}"

    full_path = landing_path(site_folder)

    if landing_type == 'local_file':
        os.makedirs(full_path, exist_ok=True)
        save_uploaded_file(file, full_path)

    landing = Landing(
        folder=site_folder,
        name=name[:255] if name else None,
        link=link[:255] if link else None,
        type=landing_type,
        tags=tags[:250] if tags else None,
        created_at=datetime.utcnow()
    )
    db.add(landing)

    try:
        db.commit()
        db.refresh(landing)
    except IntegrityError as e:
        db.rollback()

        if 'landings_folder_key' in str(e.orig):
            raise HTTPException(
                status_code=400,
                detail="A landing with this folder already exists."
            )
        if 'landings_name_key' in str(e.orig):
            raise HTTPException(
                status_code=400,
                detail="A landing with this name already exists."
            )
        raise HTTPException(
            status_code=500,
            detail="Database error: " + str(e.orig)
        )

    return {
        "status": "ok",
        "site": site_folder,
        "url": f"/landing/{site_folder}/" if landing_type == 'local_file' else link,
        "id": landing.id
    }

@router.get("/landings")
def list_landings(db: Session = Depends(get_db)):
    landings = db.query(Landing).all()
    return [
        {
            "id": landing.id,
            "folder": landing.folder,
            "name": landing.name,
            "link": landing.link,
            "type": landing.type.value if hasattr(landing.type, "value") else landing.type,  # ENUM support
            "tags": landing.tags.split(",") if landing.tags else [],
            "created_at": landing.created_at,
            "clicks": 0,           # пока мокаем
            "conversions": 0,      # пока мокаем
            "cost": 0,             # пока мокаем
            "revenue": 0,          # пока мокаем
            "roi": 0               # пока мокаем
        }
        for landing in landings
    ]

@router.get("/landing/{landing_id}")
def get_landing(landing_id: int, db: Session = Depends(get_db)):
    landing = db.query(Landing).filter(Landing.id == landing_id).first()
    if not landing:
        raise HTTPException(status_code=404, detail="Landing not found")
    return {
        "id": landing.id,
        "folder": landing.folder,
        "name": landing.name,
        "link": landing.link,
        "type": landing.type,
        "tags": landing.tags.split(",") if landing.tags else [],
        "created_at": landing.created_at
    }

@router.put("/landing/{landing_id}")
async def update_landing(
    landing_id: int,
    name: Optional[str] = Form(None),
    site_folder: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    link: Optional[str] = Form(None),
    type: Optional[int] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    type_mapping = {0: 'link', 1: 'mirror', 2: 'local_file'}

    landing = db.query(Landing).filter(Landing.id == landing_id).first()
    if not landing:
        raise HTTPException(status_code=404, detail="Landing not found")

    if name:
        landing.name = name[:255]
    if site_folder:
        landing.folder = site_folder[:255]
    if tags is not None:
        landing.tags = tags[:250] if tags else None
    if link is not None:
        landing.link = link[:255] if link else None
    if type is not None:
        landing_type = type_mapping.get(type)
        if not landing_type:
            raise HTTPException(status_code=400, detail="Invalid landing type")
        landing.type = landing_type

    folder_path = landing_path(landing.folder)

    # Если загружают новый файл
    if file:
        if landing.type != 'local_file':
            raise HTTPException(status_code=400, detail="Cannot upload file for non-local_file landing")

        # Очистка папки перед новой загрузкой
        if os.path.exists(folder_path):
            for item in os.listdir(folder_path):
                item_path = os.path.join(folder_path, item)
                if os.path.isfile(item_path):
                    os.remove(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
        else:
            os.makedirs(folder_path, exist_ok=True)

        save_uploaded_file(file, folder_path)

    try:
        db.commit()
        db.refresh(landing)
    except IntegrityError as e:
        db.rollback()

        if 'landings_folder_key' in str(e.orig):
            raise HTTPException(
                status_code=400,
                detail="A landing with this folder already exists."
            )
        if 'landings_name_key' in str(e.orig):
            raise HTTPException(
                status_code=400,
                detail="A landing with this name already exists."
            )
        raise HTTPException(
            status_code=500,
            detail="Database error: " + str(e.orig)
        )

    return {
        "status": "updated",
        "id": landing.id,
        "folder": landing.folder,
        "name": landing.name,
        "link": landing.link,
        "type": landing.type,
        "tags": landing.tags,
        "created_at": landing.created_at
    }


@router.delete("/landing/{landing_id}")
def delete_landing(landing_id: int, db: Session = Depends(get_db)):
    landing = db.query(Landing).filter(Landing.id == landing_id).first()
    if not landing:
        raise HTTPException(status_code=404, detail="Landing not found")

    folder_path = landing_path(landing.folder)
    if landing.type == 'local_file' and os.path.exists(folder_path):
        shutil.rmtree(folder_path)

    db.delete(landing)
    db.commit()

    return {"status": "deleted", "id": landing_id}
