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