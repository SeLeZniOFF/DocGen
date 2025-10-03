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