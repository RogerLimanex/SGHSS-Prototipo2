from pydantic import BaseModel, EmailStr
from datetime import date, datetime
from typing import Optional


class PatientBase(BaseModel):
    nome: str
    email: EmailStr
    telefone: Optional[str] = None
    cpf: str
    data_nascimento: date
    endereco: Optional[str] = None


class PatientCreate(PatientBase):
    pass


class PatientUpdate(BaseModel):
    nome: Optional[str] = None
    email: Optional[EmailStr] = None
    telefone: Optional[str] = None
    endereco: Optional[str] = None


class PatientResponse(PatientBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
