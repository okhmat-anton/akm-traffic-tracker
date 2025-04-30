from fastapi import APIRouter, Depends, HTTPException
from enum import Enum
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from db import get_db
from models.domain import DomainORM

router = APIRouter()

# Pydantic модель для API
class Handle404Enum(str, Enum):
    handle = 'handle'
    error = 'error'

class StatusEnum(str, Enum):
    pending = 'pending'
    success = 'success'
    error = 'error'

class DomainCreateUpdate(BaseModel):
    domain: str
    redirect_https: Optional[bool] = True
    handle_404: Handle404Enum = Handle404Enum.error
    default_company: Optional[str] = None
    group_name: Optional[str] = None

# ====== GET /domains ======
@router.get("/", response_model=List[dict])
async def get_domains(db: Session = Depends(get_db)):
    domains = db.query(DomainORM).order_by(DomainORM.id.asc()).all()
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

# ====== POST /domains ======
@router.post("/")
async def create_domain(domain: DomainCreateUpdate, db: Session = Depends(get_db)):
    try:
        new_domain = DomainORM(
            domain=domain.domain,
            redirect_https=domain.redirect_https,
            handle_404=domain.handle_404,
            default_company=domain.default_company,
            group_name=domain.group_name,
            status='pending'  # <-- СТАВИМ всегда 'pending'
        )
        db.add(new_domain)
        db.commit()
        db.refresh(new_domain)
        return {"message": "Domain created", "id": new_domain.id}
    except IntegrityError as e:
        db.rollback()
        if 'domains_domain_key' in str(e.orig):
            raise HTTPException(status_code=400, detail="A domain with this name already exists.")
        raise HTTPException(status_code=500, detail="Database error")


# ====== PATCH /domains/{domain_id} ======
@router.put("/{domain_id}")
async def update_domain(domain_id: int, domain: DomainCreateUpdate, db: Session = Depends(get_db)):
    domain_obj = db.query(DomainORM).filter(DomainORM.id == domain_id).first()
    if not domain_obj:
        raise HTTPException(status_code=404, detail="Domain not found")

    for key, value in domain.dict(exclude_unset=True).items():
        setattr(domain_obj, key, value)

    # И снова, после редактирования всегда ставим статус 'pending'
    domain_obj.status = 'pending'

    db.commit()
    db.refresh(domain_obj)
    return {"message": f"Domain {domain_id} updated"}


# ====== DELETE /domains/{domain_id} ======
@router.delete("/{domain_id}")
async def delete_domain(domain_id: int, db: Session = Depends(get_db)):
    domain_obj = db.query(DomainORM).filter(DomainORM.id == domain_id).first()
    if not domain_obj:
        raise HTTPException(status_code=404, detail="Domain not found")

    db.delete(domain_obj)
    db.commit()
    return {"message": f"Domain {domain_id} deleted"}
