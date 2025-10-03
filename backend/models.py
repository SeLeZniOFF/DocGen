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