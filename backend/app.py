from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
from fastapi.responses import FileResponse

app = FastAPI(
    title="APP API",
    description="API Documentation",
    version="1.0.0",
    docs_url="/api_docs",        # Swagger UI
    redoc_url="/api_redoc",      # ReDoc (альтернативная документация)
    openapi_url="/api_openapi.json",  # Схема OpenAPI)
    root_path="/backend"  # если сервер за прокси на пути /backend
)

# app = FastAPI() # for production

# Базовая директория проекта
BASE_DIR = Path(__file__).resolve().parent

# Настройки темы
THEMES_DIR = BASE_DIR / "themes"
THEME_NAME = "default"
THEME_DIR = THEMES_DIR / THEME_NAME
CSS_DIR = THEME_DIR / "css"
print('CSS_DIR', CSS_DIR)
# Подключение статики (картинки, стили, скрипты)
app.mount("/img", StaticFiles(directory=THEME_DIR / "img"), name="img")
app.mount("/css", StaticFiles(directory=CSS_DIR), name="css")

# Настройка шаблонов (Jinja2)
templates = Jinja2Templates(directory=THEME_DIR)

###############################################
################### STATIC ####################
###############################################
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse(THEME_DIR / "favicon.ico")


###############################################
################### PAGES #####################
###############################################


ALLOWED_PAGES = {"auth", "profile", "dashboard", "feed"}


from typing import Optional
from auth import is_authenticated, router as auth_router
from app_pages.domains import router as domains_router  # Импортируем router
from app_pages.settings import router as settings_router  # Импортируем router

# Подключаем router
app.include_router(auth_router, prefix="/api", tags=["Auth"])
app.include_router(domains_router, prefix="/api/domains", tags=["Domains"])
app.include_router(settings_router, prefix="/api/settings", tags=["Settings"])

# Router
@app.get("/", response_class=HTMLResponse)
@app.get("/{page}", response_class=HTMLResponse)
async def serve_page(request: Request, page: Optional[str] = None):
    if page is None:
        page = "auth"
    if page == "auth" and is_authenticated(request):
        page = "dashboard"
    if page not in ALLOWED_PAGES or not is_authenticated(request):
        page = "auth"  # Или можно вернуть 404
    page_file = f"pages/{page}.html"
    return templates.TemplateResponse("index.html", {
        "request": request,
        "page_to_include": page_file,
        "page": page,
        "THEME_NAME": THEME_NAME,
        "is_authenticated": is_authenticated(request),
        "page_component": '<'+page+'-page-component></'+page+'-page-component>',
    })
