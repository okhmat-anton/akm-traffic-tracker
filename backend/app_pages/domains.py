from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

# Модель данных для создания и обновления домена
class Domain(BaseModel):
    name: str
    description: Optional[str] = None

# ====== GET / ======
@router.get("/")
async def list_domains():
    return {"message": "List of all domains"}

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
