from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
from fastapi.responses import FileResponse

app = FastAPI()

# Базовая директория проекта
BASE_DIR = Path(__file__).resolve().parent

# Настройки темы
THEMES_DIR = BASE_DIR / "themes"
THEME_NAME = "main"
THEME_DIR = THEMES_DIR / THEME_NAME

print(THEME_DIR)
# Подключение статики (картинки, стили, скрипты)
app.mount("/img", StaticFiles(directory=THEME_DIR / "img"), name="img")
app.mount("/css", StaticFiles(directory=THEME_DIR / "css"), name="css")

# Настройка шаблонов (Jinja2)
templates = Jinja2Templates(directory=THEME_DIR)


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse(THEME_DIR / "favicon.ico")
# Главная страница
@app.get("/", response_class=HTMLResponse)
async def index(request: Request, page: str = "pages/auth.html"):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "page_to_include": page
    })
