from pydantic import BaseModel
from datetime import datetime


class FinanceiroBase(BaseModel):
    tipo: str  # ENTRADA ou SAIDA
    descricao: str
    valor: float


class FinanceiroResponse(FinanceiroBase):
    id: int
    data_registro: datetime

    class Config:
        orm_mode = True


class ResumoFinanceiroResponse(BaseModel):
    total_entradas: float
    total_saidas: float
    saldo: float
