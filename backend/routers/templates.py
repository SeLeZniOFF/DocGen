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