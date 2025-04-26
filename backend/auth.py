# app_pages/auth.py

from fastapi import APIRouter, Request, Response, HTTPException, status
from pydantic import BaseModel

router = APIRouter()

# Модель для передачи логина и пароля
class LoginRequest(BaseModel):
    username: str
    password: str


def is_authenticated(request: Request):
    return False

# ====== POST /login ======
@router.post("/login")
async def login(request: Request, response: Response, login_data: LoginRequest):
    if login_data.username == "admin" and login_data.password == "admin":
        response.set_cookie(key="session_token", value="valid_token", httponly=True)
        return {"message": "Login successful"}
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

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
