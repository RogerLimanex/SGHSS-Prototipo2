from pydantic import BaseModel
from datetime import date


class SuprimentoBase(BaseModel):
    nome: str
    quantidade: int
    categoria: str
    validade: date


class SuprimentoResponse(SuprimentoBase):
    id: int

    class Config:
        orm_mode = True
