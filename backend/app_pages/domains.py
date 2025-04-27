from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional

from db import fetch_domains, get_db
from sqlalchemy.orm import Session

router = APIRouter()

# Модель данных для создания и обновления домена
class Domain(BaseModel):
    name: str
    description: Optional[str] = None

# ====== GET / ======
@router.get("/", response_model=list)
async def get_domains(db: Session = Depends(get_db)):
    domains = fetch_domains(db)
    print("domains", domains)
    # Преобразуем список ORM объектов в список обычных словарей
    return [
        {
            "id": domain.id,
            "domain": domain.domain,
            "redirect_https": domain.redirect_https,
            "handle_404": domain.handle_404,
            "default_company": domain.default_company,
            "group_name": domain.group_name,
            "status": domain.status,
            "created_at": domain.created_at.isoformat() if domain.created_at else None,
            "updated_at": domain.updated_at.isoformat() if domain.updated_at else None,
        }
        for domain in domains
    ]

# ====== POST / ======
@router.post("/")
async def create_domain(domain: Domain):
    return {"message": "Domain created", "data": domain}

# ====== PATCH /{id} ======
@router.patch("/{domain_id}")
async def update_domain(domain_id: int, domain: Domain):
    return {"message": f"Domain {domain_id} updated", "data": domain}

# ====== DELETE /{id} ======
@router.delete("/{domain_id}")
async def delete_domain(domain_id: int):
    return {"message": f"Domain {domain_id} deleted"}
