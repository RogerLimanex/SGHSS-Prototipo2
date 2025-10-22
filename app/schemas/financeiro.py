# D:\ProjectSGHSS\app\schemas\financeiro.py
from pydantic import BaseModel, validator
from datetime import datetime


# ----------------------------
# Schema base para Financeiro
# ----------------------------
class FinanceiroBase(BaseModel):
    tipo: str  # ENTRADA ou SAIDA
    descricao: str
    valor: float

    @validator("valor", pre=True)
    def converter_valor(cls, v):
        """
        🔢 Converte automaticamente valores com vírgula (ex: '2500,48')
        para formato float válido (2500.48).
        Também valida se o valor é numérico.
        """
        if v is None or v == "":
            raise ValueError("O campo 'valor' é obrigatório.")
        if isinstance(v, str):
            v = v.replace(",", ".")
        try:
            return float(v)
        except ValueError:
            raise ValueError("O campo 'valor' deve ser um número válido.")


# ----------------------------
# Resposta de movimentação financeira
# ----------------------------
class FinanceiroResponse(FinanceiroBase):
    id: int
    data_registro: datetime  # compatível com o modelo SQLAlchemy

    class Config:
        orm_mode = True


# ----------------------------
# Resumo financeiro (entradas, saídas e saldo)
# ----------------------------
class ResumoFinanceiroResponse(BaseModel):
    total_entradas: float
    total_saidas: float
    saldo: float
