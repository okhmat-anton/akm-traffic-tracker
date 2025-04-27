# app_pages/auth.py
from fastapi import APIRouter, Request, Response, HTTPException, status, Depends
from pydantic import BaseModel

from sqlalchemy.orm import Session
from fastapi import Request
from jose import jwt, JWTError
from typing import Optional
from hashlib import md5
from db import get_db, get_user, SessionLocal
from hashlib import md5
from datetime import datetime, timedelta

from models.user import User

router = APIRouter()

# Конфигурация JWT
SECRET_KEY = "your-super-secret-key-for-jwt"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 2400
pass_salt = 'akm_'


# Генерация токена
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# Модель для передачи логина и пароля
class LoginRequest(BaseModel):
    username: str
    password: str


# Секретный ключ для подписи токенов
SECRET_KEY = "your-super-secret-key"
ALGORITHM = "HS256"

# Фейковая база пользователей
fake_users_db = {
    "admin": {
        "username": "admin",
        "password_hash": md5("akm_admin".encode()).hexdigest()
    },
    "user1": {
        "username": "user1",
        "password_hash": md5("akm_user".encode()).hexdigest()
    }
}


# ====== Проверка авторизации ======
def is_authenticated(request: Request) -> bool:
    token = request.cookies.get("session_token")
    if not token:
        return False

    try:
        # Декодируем JWT токен
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")

        if not username:
            return False

        db: Session = SessionLocal()
        user = get_user(db, username)
        db.close()
        if user:
            return True
        else:
            return False


    except JWTError:
        return False


# ====== POST /login ======
@router.post("/login")
async def login(request: Request, response: Response, login_data: LoginRequest, db: Session = Depends(get_db)):
    user = get_user(db, login_data.username)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    # Хешируем пароль как "akm" + password
    hashed_password = md5((pass_salt + login_data.password).encode()).hexdigest()

    if user.password_hash != hashed_password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials 2")

    # Генерируем токен
    token_data = {"sub": user.username}
    token = create_access_token(data=token_data)

    # Сохраняем токен в куках
    response.set_cookie(key="session_token", value=token, httponly=True)

    return {"message": "Login successful"}


# ====== POST /logout ======
@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(key="session_token")
    return {"message": "Logged out"}


# ====== GET /status ======
@router.get("/status")
async def auth_status(request: Request):
    token = request.cookies.get("session_token")
    if token == "valid_token":
        return {"authenticated": True}
    return {"authenticated": False}
