from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON
from app.db.session import Base
import datetime

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Patient(Base):
    __tablename__ = 'patients'
    id = Column(Integer, primary_key=True)
    nome = Column(String)
    cpf_encrypted = Column(String, nullable=True)
    data_nascimento = Column(DateTime, nullable=True)
    contact = Column(JSON, nullable=True)
