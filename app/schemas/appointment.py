# app/schemas/appointment.py
from pydantic import BaseModel
from datetime import date, time
from typing import Optional


class AppointmentBase(BaseModel):
    patient_id: int
    doctor_id: int
    data_consulta: date
    hora_consulta: time
    duracao_minutos: Optional[int] = 30
    observacoes: Optional[str] = None


class AppointmentCreate(AppointmentBase):
    pass


class AppointmentUpdate(BaseModel):
    data_consulta: Optional[date] = None
    hora_consulta: Optional[time] = None
    duracao_minutos: Optional[int] = None
    observacoes: Optional[str] = None
    status: Optional[str] = None


class AppointmentResponse(AppointmentBase):
    id: int
    status: str

    class Config:
        from_attributes = True
