from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.models import AppointmentStatus


class TeleconsultationBase(BaseModel):
    appointment_id: int
    link_video: Optional[str] = None
    data_hora: Optional[datetime] = None
    status: Optional[AppointmentStatus] = AppointmentStatus.AGENDADA


class TeleconsultationCreate(TeleconsultationBase):
    pass


class TeleconsultationResponse(TeleconsultationBase):
    id: int

    class Config:
        orm_mode = True
