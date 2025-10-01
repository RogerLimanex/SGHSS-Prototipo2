from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class PrescriptionBase(BaseModel):
    patient_id: int
    doctor_id: int
    medicamento: str
    dosagem: str
    instrucoes: Optional[str] = None


class PrescriptionCreate(PrescriptionBase):
    pass


class PrescriptionResponse(PrescriptionBase):
    id: int
    data_hora: datetime

    class Config:
        orm_mode = True
