from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from pathlib import Path

from .database import Base, engine
from .routers import entities, clients, values, templates, generate

# Создаем таблицы при старте (для простоты вместо Alembic)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="DOCX Template Generator", version="1.0.0")

# CORS (при необходимости изменить домены)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"]
    ,allow_headers=["*"]
)

# Роутеры API
app.include_router(entities.router, prefix="/entities", tags=["entities"])
app.include_router(clients.router, prefix="/clients", tags=["clients"])
app.include_router(values.router, prefix="/values", tags=["values"])
app.include_router(templates.router, prefix="/templates", tags=["templates"])
app.include_router(generate.router, prefix="/generate", tags=["generate"])

# Статика (простой фронтенд)
static_dir = Path(__file__).parent / "static"
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

# Доп. редирект на UI, если кто-то вызвал корень API на /api
@app.get("/api")
async def api_root():
    return RedirectResponse("/")