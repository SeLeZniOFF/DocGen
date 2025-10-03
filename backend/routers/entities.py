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