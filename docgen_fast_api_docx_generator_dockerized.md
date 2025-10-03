# Проект: Генератор DOCX по шаблонам (FastAPI + PostgreSQL + SQLAlchemy + python-docx + Docker)

Ниже — полный код проекта, готовый к запуску. Скопируй структуру файлов как указано. В конце — полные инструкции по запуску на Ubuntu «с нуля» и команды для упаковки проекта в ZIP.

---

## Структура проекта
```
docgen/
├─ backend/
│  ├─ main.py
│  ├─ database.py
│  ├─ models.py
│  ├─ schemas.py
│  ├─ crud.py
│  ├─ docx_utils.py
│  ├─ routers/
│  │  ├─ entities.py
│  │  ├─ clients.py
│  │  ├─ values.py
│  │  ├─ templates.py
│  │  └─ generate.py
│  ├─ static/
│  │  └─ index.html
│  └─ storage/
│     ├─ templates/        # сюда сохраняются загруженные шаблоны
│     └─ outputs/          # сюда сохраняются сгенерированные документы
├─ requirements.txt
├─ Dockerfile
├─ docker-compose.yml
├─ .env.example
└─ README.md
```

---

## Файл: `backend/main.py`
```python
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
```

---

## Файл: `backend/database.py`
```python
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://docgen:docgen@db:5432/docgen")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Зависимость для FastAPI
from contextlib import contextmanager

@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

---

## Файл: `backend/models.py`
```python
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    histories = relationship("GenerationHistory", back_populates="user")

class Client(Base):
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    values = relationship("Value", back_populates="client", cascade="all, delete-orphan")
    histories = relationship("GenerationHistory", back_populates="client")

class Entity(Base):
    __tablename__ = "entities"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(255), unique=True, nullable=False)  # например {FIO}
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    values = relationship("Value", back_populates="entity", cascade="all, delete-orphan")

class Value(Base):
    __tablename__ = "values"
    id = Column(Integer, primary_key=True, index=True)
    entity_id = Column(Integer, ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    value_text = Column(Text, nullable=False)

    entity = relationship("Entity", back_populates="values")
    client = relationship("Client", back_populates="values")

    __table_args__ = (
        UniqueConstraint("entity_id", "client_id", name="uq_value_entity_client"),
    )

class Template(Base):
    __tablename__ = "templates"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    filename = Column(String(500), nullable=False)
    stored_path = Column(String(1000), nullable=False)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

class GenerationHistory(Base):
    __tablename__ = "generation_history"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    template_id = Column(Integer, ForeignKey("templates.id"), nullable=False)
    output_filename = Column(String(500), nullable=False)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="histories")
    client = relationship("Client", back_populates="histories")
```

---

## Файл: `backend/schemas.py`
```python
from typing import Optional, List
from pydantic import BaseModel

# Entities
class EntityBase(BaseModel):
    name: str
    code: str

class EntityCreate(EntityBase):
    pass

class EntityUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None

class EntityOut(EntityBase):
    id: int
    class Config:
        from_attributes = True

# Clients
class ClientBase(BaseModel):
    name: str

class ClientCreate(ClientBase):
    pass

class ClientUpdate(BaseModel):
    name: Optional[str] = None

class ClientOut(ClientBase):
    id: int
    class Config:
        from_attributes = True

# Values
class ValueBase(BaseModel):
    entity_id: int
    client_id: int
    value_text: str

class ValueCreate(ValueBase):
    pass

class ValueUpdate(BaseModel):
    value_text: Optional[str] = None

class ValueOut(ValueBase):
    id: int
    class Config:
        from_attributes = True

# Templates
class TemplateOut(BaseModel):
    id: int
    name: str
    filename: str
    stored_path: str
    class Config:
        from_attributes = True

# Generate
class GenerateRequest(BaseModel):
    template_id: int
    client_ids: List[int]
    # optional: user_id для истории
    user_id: Optional[int] = None
```

---

## Файл: `backend/crud.py`
```python
from typing import List, Optional
from sqlalchemy.orm import Session
from . import models

# Entities
def create_entity(db: Session, name: str, code: str) -> models.Entity:
    ent = models.Entity(name=name, code=code)
    db.add(ent)
    db.commit()
    db.refresh(ent)
    return ent

def get_entities(db: Session) -> List[models.Entity]:
    return db.query(models.Entity).order_by(models.Entity.id.desc()).all()

def get_entity(db: Session, entity_id: int) -> Optional[models.Entity]:
    return db.query(models.Entity).filter(models.Entity.id == entity_id).first()

def update_entity(db: Session, entity_id: int, **kwargs) -> Optional[models.Entity]:
    ent = get_entity(db, entity_id)
    if not ent:
        return None
    for k, v in kwargs.items():
        if v is not None:
            setattr(ent, k, v)
    db.commit()
    db.refresh(ent)
    return ent

def delete_entity(db: Session, entity_id: int) -> bool:
    ent = get_entity(db, entity_id)
    if not ent:
        return False
    db.delete(ent)
    db.commit()
    return True

# Clients

def create_client(db: Session, name: str) -> models.Client:
    c = models.Client(name=name)
    db.add(c)
    db.commit()
    db.refresh(c)
    return c

def get_clients(db: Session) -> List[models.Client]:
    return db.query(models.Client).order_by(models.Client.id.desc()).all()

def get_client(db: Session, client_id: int) -> Optional[models.Client]:
    return db.query(models.Client).filter(models.Client.id == client_id).first()

def update_client(db: Session, client_id: int, **kwargs) -> Optional[models.Client]:
    c = get_client(db, client_id)
    if not c:
        return None
    for k, v in kwargs.items():
        if v is not None:
            setattr(c, k, v)
    db.commit()
    db.refresh(c)
    return c

def delete_client(db: Session, client_id: int) -> bool:
    c = get_client(db, client_id)
    if not c:
        return False
    db.delete(c)
    db.commit()
    return True

# Values

def set_value(db: Session, entity_id: int, client_id: int, value_text: str) -> models.Value:
    existing = db.query(models.Value).filter(
        models.Value.entity_id == entity_id,
        models.Value.client_id == client_id
    ).first()
    if existing:
        existing.value_text = value_text
        db.commit()
        db.refresh(existing)
        return existing
    v = models.Value(entity_id=entity_id, client_id=client_id, value_text=value_text)
    db.add(v)
    db.commit()
    db.refresh(v)
    return v

def get_values(db: Session, client_id: Optional[int] = None) -> List[models.Value]:
    q = db.query(models.Value)
    if client_id is not None:
        q = q.filter(models.Value.client_id == client_id)
    return q.order_by(models.Value.id.desc()).all()

def delete_value(db: Session, value_id: int) -> bool:
    v = db.query(models.Value).filter(models.Value.id == value_id).first()
    if not v:
        return False
    db.delete(v)
    db.commit()
    return True

# Templates & History

def add_template(db: Session, name: str, filename: str, stored_path: str) -> models.Template:
    t = models.Template(name=name, filename=filename, stored_path=stored_path)
    db.add(t)
    db.commit()
    db.refresh(t)
    return t

def list_templates(db: Session) -> List[models.Template]:
    return db.query(models.Template).order_by(models.Template.id.desc()).all()

def add_history(db: Session, user_id: Optional[int], client_id: int, template_id: int, output_filename: str) -> models.GenerationHistory:
    h = models.GenerationHistory(user_id=user_id, client_id=client_id, template_id=template_id, output_filename=output_filename)
    db.add(h)
    db.commit()
    db.refresh(h)
    return h
```

---

## Файл: `backend/docx_utils.py`
```python
import re
from typing import Dict, Set
from docx import Document
from docx.table import _Cell
from docx.text.paragraph import Paragraph

PLACEHOLDER_RE = re.compile(r"\{[A-Z0-9_]+\}")


def find_placeholders_in_text(text: str) -> Set[str]:
    return set(PLACEHOLDER_RE.findall(text or ""))


def iter_paragraphs_and_cells(doc: Document):
    # Параграфы
    for p in doc.paragraphs:
        yield p
    # Таблицы
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    yield p


def replace_placeholders(doc: Document, mapping: Dict[str, str]):
    """ Аккуратно заменяет плейсхолдеры, с учетом разбиения на runs. """
    for p in iter_paragraphs_and_cells(doc):
        replace_in_paragraph(p, mapping)


def replace_in_paragraph(paragraph: Paragraph, mapping: Dict[str, str]):
    # Склеиваем все runs в один текст, запоминаем границы
    full_text = "".join(run.text for run in paragraph.runs)
    if not full_text:
        return
    placeholders = find_placeholders_in_text(full_text)
    if not placeholders:
        return
    # Замена всех найденных
    for ph in placeholders:
        if ph in mapping:
            full_text = full_text.replace(ph, mapping[ph])
    # Переписываем в один run
    for _ in range(len(paragraph.runs) - 1):
        paragraph.runs[0].merge(paragraph.runs[1])
    paragraph.runs[0].text = full_text


def extract_placeholders(doc: Document) -> Set[str]:
    found = set()
    for p in iter_paragraphs_and_cells(doc):
        found |= find_placeholders_in_text(p.text)
    return found
```

---

## Файл: `backend/routers/entities.py`
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from .. import crud, schemas

router = APIRouter()

@router.get("/", response_model=list[schemas.EntityOut])
def list_entities(db: Session = Depends(get_db)):
    return crud.get_entities(db)

@router.post("/", response_model=schemas.EntityOut)
def create_entity(payload: schemas.EntityCreate, db: Session = Depends(get_db)):
    return crud.create_entity(db, name=payload.name, code=payload.code)

@router.put("/{entity_id}", response_model=schemas.EntityOut)
def update_entity(entity_id: int, payload: schemas.EntityUpdate, db: Session = Depends(get_db)):
    ent = crud.update_entity(db, entity_id, name=payload.name, code=payload.code)
    if not ent:
        raise HTTPException(status_code=404, detail="Entity not found")
    return ent

@router.delete("/{entity_id}")
def delete_entity(entity_id: int, db: Session = Depends(get_db)):
    ok = crud.delete_entity(db, entity_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Entity not found")
    return {"status": "deleted"}
```

---

## Файл: `backend/routers/clients.py`
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from .. import crud, schemas

router = APIRouter()

@router.get("/", response_model=list[schemas.ClientOut])
def list_clients(db: Session = Depends(get_db)):
    return crud.get_clients(db)

@router.post("/", response_model=schemas.ClientOut)
def create_client(payload: schemas.ClientCreate, db: Session = Depends(get_db)):
    return crud.create_client(db, name=payload.name)

@router.put("/{client_id}", response_model=schemas.ClientOut)
def update_client(client_id: int, payload: schemas.ClientUpdate, db: Session = Depends(get_db)):
    c = crud.update_client(db, client_id, name=payload.name)
    if not c:
        raise HTTPException(status_code=404, detail="Client not found")
    return c

@router.delete("/{client_id}")
def delete_client(client_id: int, db: Session = Depends(get_db)):
    ok = crud.delete_client(db, client_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Client not found")
    return {"status": "deleted"}
```

---

## Файл: `backend/routers/values.py`
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from .. import crud, schemas

router = APIRouter()

@router.get("/", response_model=list[schemas.ValueOut])
def list_values(client_id: int | None = None, db: Session = Depends(get_db)):
    return crud.get_values(db, client_id=client_id)

@router.post("/", response_model=schemas.ValueOut)
def upsert_value(payload: schemas.ValueCreate, db: Session = Depends(get_db)):
    return crud.set_value(db, entity_id=payload.entity_id, client_id=payload.client_id, value_text=payload.value_text)

@router.delete("/{value_id}")
def delete_value(value_id: int, db: Session = Depends(get_db)):
    ok = crud.delete_value(db, value_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Value not found")
    return {"status": "deleted"}
```

---

## Файл: `backend/routers/templates.py`
```python
import os
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from .. import crud, schemas

router = APIRouter()

STORAGE_ROOT = Path(__file__).resolve().parents[1] / "storage"
TEMPLATES_DIR = STORAGE_ROOT / "templates"
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

@router.get("/", response_model=list[schemas.TemplateOut])
def list_templates(db: Session = Depends(get_db)):
    return crud.list_templates(db)

@router.post("/upload", response_model=schemas.TemplateOut)
async def upload_template(name: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith(".docx"):
        raise HTTPException(status_code=400, detail="Only .docx files are allowed")
    dest = TEMPLATES_DIR / file.filename
    # если файл с таким именем существует — дополним индексом
    i = 1
    while dest.exists():
        dest = TEMPLATES_DIR / f"{dest.stem}_{i}{dest.suffix}"
        i += 1
    content = await file.read()
    with open(dest, "wb") as f:
        f.write(content)
    t = crud.add_template(db, name=name, filename=dest.name, stored_path=str(dest))
    return t
```

---

## Файл: `backend/routers/generate.py`
```python
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from docx import Document

from ..database import get_db
from .. import crud, models, schemas
from ..docx_utils import extract_placeholders, replace_placeholders

router = APIRouter()

STORAGE_ROOT = Path(__file__).resolve().parents[1] / "storage"
OUTPUTS_DIR = STORAGE_ROOT / "outputs"
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/", response_class=StreamingResponse)
def generate(payload: schemas.GenerateRequest, db: Session = Depends(get_db)):
    # Проверяем шаблон
    t = db.query(models.Template).filter(models.Template.id == payload.template_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Template not found")

    # Читаем документ шаблона
    doc = Document(t.stored_path)
    placeholders = extract_placeholders(doc)

    # Массовая генерация
    if len(payload.client_ids) > 1:
        mem_zip = BytesIO()
        with ZipFile(mem_zip, mode="w", compression=ZIP_DEFLATED) as zf:
            for cid in payload.client_ids:
                rendered_path = render_for_client(db, cid, t, doc, placeholders)
                zf.write(rendered_path, arcname=Path(rendered_path).name)
        mem_zip.seek(0)
        headers = {"Content-Disposition": "attachment; filename=generated_documents.zip"}
        return StreamingResponse(mem_zip, media_type="application/zip", headers=headers)

    # Одиночная генерация
    client_id = payload.client_ids[0]
    rendered_path = render_for_client(db, client_id, t, doc, placeholders)
    return FileResponse(rendered_path, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", filename=Path(rendered_path).name)


def render_for_client(db: Session, client_id: int, template: models.Template, base_doc: Document, placeholders: set[str]) -> str:
    client = db.query(models.Client).filter(models.Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail=f"Client {client_id} not found")

    # Создаем mapping {CODE: value}
    mapping = {}
    for ph in placeholders:
        code = ph  # в БД code хранится вместе с фигурными скобками, например {FIO}
        ent = db.query(models.Entity).filter(models.Entity.code == code).first()
        if ent:
            val = db.query(models.Value).filter(models.Value.entity_id == ent.id, models.Value.client_id == client.id).first()
            if val:
                mapping[code] = val.value_text

    # Копия документа
    from copy import deepcopy
    doc = deepcopy(base_doc)

    # Замены
    replace_placeholders(doc, mapping)

    # Если есть незаполненные плейсхолдеры — оставляем как есть (или можно бросить ошибку)
    # Сохраняем документ
    safe_client = str(client.name).replace(" ", "_")
    out_name = f"{Path(template.filename).stem}__{safe_client}.docx"
    out_path = OUTPUTS_DIR / out_name
    doc.save(out_path)

    # История
    crud.add_history(db, user_id=None, client_id=client.id, template_id=template.id, output_filename=out_name)

    return str(out_path)
```

---

## Файл: `backend/static/index.html`
```html
<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>DOCX Generator</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet" />
</head>
<body class="bg-light">
<div class="container py-4">
  <h1 class="mb-4">DOCX Generator</h1>

  <div class="row g-4">
    <!-- Entities -->
    <div class="col-md-6">
      <div class="card shadow-sm">
        <div class="card-header">Сущности</div>
        <div class="card-body">
          <form id="entityForm" class="row g-2">
            <div class="col-5">
              <input class="form-control" placeholder="Название (ФИО)" id="entName" required />
            </div>
            <div class="col-5">
              <input class="form-control" placeholder="Код ({FIO})" id="entCode" required />
            </div>
            <div class="col-2 d-grid">
              <button class="btn btn-primary" type="submit">Добавить</button>
            </div>
          </form>
          <hr />
          <ul class="list-group" id="entitiesList"></ul>
        </div>
      </div>
    </div>

    <!-- Clients -->
    <div class="col-md-6">
      <div class="card shadow-sm">
        <div class="card-header">Клиенты</div>
        <div class="card-body">
          <form id="clientForm" class="row g-2">
            <div class="col-9">
              <input class="form-control" placeholder="Имя клиента" id="clientName" required />
            </div>
            <div class="col-3 d-grid">
              <button class="btn btn-primary" type="submit">Добавить</button>
            </div>
          </form>
          <hr />
          <ul class="list-group" id="clientsList"></ul>
        </div>
      </div>
    </div>

    <!-- Values -->
    <div class="col-md-12">
      <div class="card shadow-sm">
        <div class="card-header">Значения для клиента</div>
        <div class="card-body">
          <div class="row g-2 align-items-end">
            <div class="col-md-3">
              <label class="form-label">Клиент</label>
              <select class="form-select" id="valClient"></select>
            </div>
            <div class="col-md-3">
              <label class="form-label">Сущность</label>
              <select class="form-select" id="valEntity"></select>
            </div>
            <div class="col-md-4">
              <label class="form-label">Значение</label>
              <input class="form-control" id="valText" />
            </div>
            <div class="col-md-2 d-grid">
              <button class="btn btn-primary" id="btnSetValue">Сохранить</button>
            </div>
          </div>
          <hr />
          <div id="valuesList" class="small"></div>
        </div>
      </div>
    </div>

    <!-- Templates & Generate -->
    <div class="col-md-12">
      <div class="card shadow-sm">
        <div class="card-header">Шаблоны и генерация</div>
        <div class="card-body">
          <div class="row g-2">
            <div class="col-md-6">
              <form id="tplForm" class="row g-2" enctype="multipart/form-data">
                <div class="col-5">
                  <input class="form-control" placeholder="Название шаблона" id="tplName" required />
                </div>
                <div class="col-5">
                  <input type="file" class="form-control" id="tplFile" accept=".docx" required />
                </div>
                <div class="col-2 d-grid">
                  <button class="btn btn-secondary" type="submit">Загрузить</button>
                </div>
              </form>
              <ul class="list-group mt-3" id="tplList"></ul>
            </div>
            <div class="col-md-6">
              <label class="form-label">Клиенты для генерации</label>
              <select class="form-select" id="genClients" multiple size="6"></select>
              <label class="form-label mt-2">Шаблон</label>
              <select class="form-select" id="genTemplate"></select>
              <button class="btn btn-success mt-3" id="btnGenerate">Сгенерировать</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>

<script>
const api = '';

async function fetchJSON(url, opts) {
  const r = await fetch(url, opts);
  if (!r.ok) throw new Error(await r.text());
  return r.headers.get('content-type')?.includes('application/json') ? r.json() : r;
}

async function loadEntities() {
  const data = await fetchJSON('/entities/');
  const list = document.getElementById('entitiesList');
  const sel = document.getElementById('valEntity');
  list.innerHTML = '';
  sel.innerHTML = '';
  data.forEach(e => {
    const li = document.createElement('li');
    li.className = 'list-group-item d-flex justify-content-between align-items-center';
    li.innerHTML = `<span><code>${e.code}</code> — ${e.name}</span> <span class="badge bg-light text-dark">id ${e.id}</span>`;
    list.appendChild(li);

    const opt = document.createElement('option');
    opt.value = e.id; opt.textContent = `${e.name} ${e.code}`;
    sel.appendChild(opt);
  });
}

async function loadClients() {
  const data = await fetchJSON('/clients/');
  const list = document.getElementById('clientsList');
  const sel1 = document.getElementById('valClient');
  const sel2 = document.getElementById('genClients');
  list.innerHTML = '';
  sel1.innerHTML = '';
  sel2.innerHTML = '';
  data.forEach(c => {
    const li = document.createElement('li');
    li.className = 'list-group-item d-flex justify-content-between align-items-center';
    li.innerHTML = `<span>${c.name}</span> <span class="badge bg-light text-dark">id ${c.id}</span>`;
    list.appendChild(li);

    const o1 = document.createElement('option'); o1.value = c.id; o1.textContent = c.name; sel1.appendChild(o1);
    const o2 = document.createElement('option'); o2.value = c.id; o2.textContent = c.name; sel2.appendChild(o2);
  });
  loadValues();
}

async function loadValues() {
  const clientId = document.getElementById('valClient').value;
  if (!clientId) return;
  const data = await fetchJSON(`/values/?client_id=${clientId}`);
  const box = document.getElementById('valuesList');
  box.innerHTML = data.map(v => `<code>[${v.entity_id}]</code> ${v.value_text}`).join('<br/>');
}

async function loadTemplates() {
  const data = await fetchJSON('/templates/');
  const list = document.getElementById('tplList');
  const sel = document.getElementById('genTemplate');
  list.innerHTML = '';
  sel.innerHTML = '';
  data.forEach(t => {
    const li = document.createElement('li');
    li.className = 'list-group-item d-flex justify-content-between align-items-center';
    li.innerHTML = `<span>${t.name}</span> <span class="badge bg-light text-dark">${t.filename}</span>`;
    list.appendChild(li);

    const opt = document.createElement('option'); opt.value = t.id; opt.textContent = `${t.name} (${t.filename})`; sel.appendChild(opt);
  });
}

// forms

document.getElementById('entityForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const name = document.getElementById('entName').value.trim();
  const code = document.getElementById('entCode').value.trim();
  await fetchJSON('/entities/', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({name, code})});
  e.target.reset();
  loadEntities();
});

document.getElementById('clientForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const name = document.getElementById('clientName').value.trim();
  await fetchJSON('/clients/', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({name})});
  e.target.reset();
  loadClients();
});

// values

document.getElementById('valClient').addEventListener('change', loadValues);

document.getElementById('btnSetValue').addEventListener('click', async () => {
  const entity_id = +document.getElementById('valEntity').value;
  const client_id = +document.getElementById('valClient').value;
  const value_text = document.getElementById('valText').value;
  await fetchJSON('/values/', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({entity_id, client_id, value_text})});
  document.getElementById('valText').value = '';
  loadValues();
});

// templates

document.getElementById('tplForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const name = document.getElementById('tplName').value.trim();
  const file = document.getElementById('tplFile').files[0];
  const fd = new FormData();
  fd.append('name', name);
  fd.append('file', file);
  await fetchJSON('/templates/upload', {method:'POST', body: fd});
  e.target.reset();
  loadTemplates();
});

// generate

document.getElementById('btnGenerate').addEventListener('click', async () => {
  const genTemplate = +document.getElementById('genTemplate').value;
  const genClients = Array.from(document.getElementById('genClients').selectedOptions).map(o => +o.value);
  if (!genTemplate || genClients.length === 0) { alert('Выберите шаблон и хотя бы одного клиента'); return; }
  const resp = await fetch('/generate/', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({template_id: genTemplate, client_ids: genClients})});
  if (!resp.ok) { alert('Ошибка генерации'); return; }
  const blob = await resp.blob();
  let filename = 'generated';
  const disp = resp.headers.get('Content-Disposition');
  if (disp) { const m = /filename=([^;]+)/i.exec(disp); if (m) filename = m[1]; }
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  a.click();
});

// initial load
loadEntities();
loadClients();
loadTemplates();
</script>
</body>
</html>
```

---

## Файл: `requirements.txt`
```txt
fastapi==0.115.0
uvicorn[standard]==0.30.6
SQLAlchemy==2.0.34
psycopg2-binary==2.9.9
python-docx==1.1.2
python-multipart==0.0.9
```

---

## Файл: `Dockerfile`
```dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Системные зависимости для psycopg2 и lxml (исп. в python-docx)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libxml2 \
    libxslt1.1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend ./backend

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Файл: `docker-compose.yml`
```yaml
version: "3.9"
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-docgen}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-docgen}
      POSTGRES_DB: ${POSTGRES_DB:-docgen}
    volumes:
      - db_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  backend:
    build: .
    environment:
      DATABASE_URL: ${DATABASE_URL:-postgresql+psycopg2://docgen:docgen@db:5432/docgen}
    volumes:
      - ./backend/storage:/app/backend/storage
    depends_on:
      - db
    ports:
      - "8000:8000"

volumes:
  db_data:
```

---

## Файл: `.env.example`
```dotenv
# Значения по умолчанию уже заложены в docker-compose.yml
POSTGRES_USER=docgen
POSTGRES_PASSWORD=docgen
POSTGRES_DB=docgen
DATABASE_URL=postgresql+psycopg2://docgen:docgen@db:5432/docgen
```

---

## Файл: `README.md`
```md
# DOCX Template Generator

FastAPI + PostgreSQL + SQLAlchemy + python-docx + простой UI (Bootstrap). Генерирует Word-документы по загруженным шаблонам с плейсхолдерами вида `{FIO}`, `{ADDRESS}`, и т.д., подставляя значения из БД для выбранного клиента(ов).

## Возможности
- CRUD сущностей (имя + код `{CODE}`)
- CRUD клиентов
- Значения сущности для клиента (один клиент — набор значений)
- Загрузка шаблонов `.docx`
- Поиск и замена плейсхолдеров в тексте и таблицах
- Генерация для одного клиента (возврат `.docx`) или для нескольких (возврат `.zip`)
- История генераций в БД

## Быстрый старт (Docker)

```bash
# 1) Клонируйте репозиторий/скопируйте файлы
cd docgen

# 2) (опционально) создайте .env на базе .env.example
cp .env.example .env

# 3) Поднимите контейнеры
docker compose up --build -d

# 4) Откройте UI
# http://localhost:8000
```

### Полный путь запуска на чистой Ubuntu
```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker

# Установка Docker Compose plugin (если не установился вместе с Docker)
sudo apt-get install -y docker-compose-plugin

# Скачайте/скопируйте проект в ~/docgen
mkdir -p ~/docgen && cd ~/docgen
# ... поместите сюда файлы как в структуре проекта ...

# Запуск
docker compose up --build -d

# Проверка
docker compose logs -f backend
# Откройте в браузере http://SERVER_IP:8000
```

## Как пользоваться UI
1. **Сущности**: добавьте, например, `Название: ФИО`, `Код: {FIO}`.
2. **Клиенты**: добавьте клиента, например, `Иванов Иван`.
3. **Значения**: выберите клиента, сущность `{FIO}`, введите значение `Иванов Иван Иваныч`, нажмите «Сохранить».
4. **Шаблон**: загрузите `.docx`, содержащий текст вроде `Настоящим подтверждается, что {FIO} проживает по адресу {ADDRESS}`.
5. **Генерация**: выберите одного или нескольких клиентов + шаблон. Нажмите «Сгенерировать». Получите `.docx` или `.zip`.

## Примечания
- Коды сущностей должны включать фигурные скобки: `{FIO}`, `{ADDRESS}` и т.п.
- Если значение для кода у клиента отсутствует — плейсхолдер останется как есть в документе.
- Шаблоны и результаты сохраняются в `backend/storage/templates` и `backend/storage/outputs` (примонтированы в volume).

## Упаковка в ZIP
Из корня проекта (где `docker-compose.yml`):
```bash
zip -r docgen.zip . -x "*/__pycache__/*" -x "*.pyc" -x "*.DS_Store"
```

Готово: `docgen.zip` можно отправлять и разворачивать на другой машине.
```

