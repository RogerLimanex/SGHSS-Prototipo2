from pydantic import BaseModel
from typing import Optional


class LeitoBase(BaseModel):
    numero: str
    status: str
    paciente_id: Optional[int] = None


class LeitoResponse(LeitoBase):
    id: int

    class Config:
        orm_mode = True
