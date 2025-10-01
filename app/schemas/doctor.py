from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class DoctorBase(BaseModel):
    nome: str
    email: EmailStr
    telefone: Optional[str] = None
    crm: str
    especialidade: str


class DoctorCreate(DoctorBase):
    pass


class DoctorUpdate(BaseModel):
    nome: Optional[str] = None
    email: Optional[EmailStr] = None
    telefone: Optional[str] = None
    especialidade: Optional[str] = None
    active: Optional[bool] = None


class DoctorResponse(DoctorBase):
    id: int
    active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

