from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from hashlib import md5
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from db import get_db
from models.user import UserORM

router = APIRouter()

pass_salt = 'akm_'
# Pydantic модели

class UserOut(BaseModel):
    id: int
    username: str
    email: Optional[EmailStr]
    is_admin: bool
    active: bool

    class Config:
        orm_mode = True

class UserCreateUpdate(BaseModel):
    username: str
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    is_admin: Optional[bool] = False
    active: Optional[bool] = True

# ====== Получить всех пользователей ======

@router.get("/", response_model=List[UserOut])
def get_users(db: Session = Depends(get_db)):
    return db.query(UserORM).order_by(UserORM.id.desc()).all()

# ====== Создать пользователя ======

@router.post("/")
def create_user(user: UserCreateUpdate, db: Session = Depends(get_db)):
    if not user.password:
        raise HTTPException(status_code=400, detail="Password is required")

    if user.username.lower() == "tracker_admin":
        raise HTTPException(status_code=403, detail="Cannot create tracker_admin user")

    password_hash = md5((pass_salt + user.password).encode()).hexdigest()

    new_user = UserORM(
        username=user.username,
        email=user.email,
        password_hash=password_hash,
        is_admin=False,
        active=user.active
    )

    db.add(new_user)
    try:
        db.commit()
        db.refresh(new_user)
        return {"message": "User created", "id": new_user.id}
    except IntegrityError as e:
        db.rollback()
        if 'users_username_key' in str(e.orig):
            raise HTTPException(status_code=400, detail="Username already exists.")
        if 'users_email_key' in str(e.orig):
            raise HTTPException(status_code=400, detail="Email already exists.")
        raise HTTPException(status_code=500, detail="Database error")

# ====== Обновить пользователя ======

@router.patch("/{user_id}")
def update_user(user_id: int, user: UserCreateUpdate, db: Session = Depends(get_db)):
    user_obj = db.query(UserORM).filter(UserORM.id == user_id).first()
    if not user_obj:
        raise HTTPException(status_code=404, detail="User not found")

    if user_obj.username.lower() == "tracker_admin":
        raise HTTPException(status_code=403, detail="tracker_admin cannot be edited")

    if user.email is not None:
        user_obj.email = user.email
    if user.is_admin is not None:
        user_obj.is_admin = user.is_admin
    if user.active is not None:
        user_obj.active = user.active
    if user.password:
        user_obj.password_hash = md5((pass_salt + user.password).encode()).hexdigest()

    if user_obj.username.lower() != "tracker_admin":
        user.is_admin = False
    else:
        user.is_admin = True

    db.commit()
    db.refresh(user_obj)
    return {"message": "User updated"}

# ====== Удалить пользователя ======

@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user_obj = db.query(UserORM).filter(UserORM.id == user_id).first()
    if not user_obj:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user_obj)
    db.commit()
    return {"message": "User deleted"}
