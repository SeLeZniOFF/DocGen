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