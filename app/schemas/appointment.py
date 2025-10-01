from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.models import AppointmentStatus


class AppointmentBase(BaseModel):
    patient_id: int
    doctor_id: int
    data_hora: datetime
    duracao_minutos: Optional[int] = 30
    status: Optional[AppointmentStatus] = AppointmentStatus.AGENDADA
    observacoes: Optional[str] = None


class AppointmentCreate(AppointmentBase):
    pass


class AppointmentResponse(AppointmentBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
