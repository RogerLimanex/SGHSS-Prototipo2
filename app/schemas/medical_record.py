from pydantic import BaseModel
from datetime import datetime


class MedicalRecordBase(BaseModel):
    patient_id: int
    doctor_id: int
    descricao: str


class MedicalRecordCreate(MedicalRecordBase):
    pass


class MedicalRecordResponse(MedicalRecordBase):
    id: int
    data_hora: datetime

    class Config:
        orm_mode = True
