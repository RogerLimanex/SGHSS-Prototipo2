from pydantic import BaseModel, validator  # BaseModel para schemas e validator para validações personalizadas
from datetime import datetime  # datetime para datas


# ----------------------------
# Schema base para Financeiro
# ----------------------------
class FinanceiroBase(BaseModel):
    tipo: str  # Tipo da movimentação: ENTRADA ou SAIDA
    descricao: str  # Descrição da movimentação
    valor: float  # Valor da movimentação

    @validator("valor", pre=True)
    def converter_valor(cls, v):
        """
        🔢 Converte valores com vírgula (ex: '2500,48') para float (2500.48)
        e valida se o valor é numérico.
        """
        if v is None or v == "":
            raise ValueError("O campo 'valor' é obrigatório.")
        if isinstance(v, str):
            v = v.replace(",", ".")  # substitui vírgula por ponto
        try:
            return float(v)
        except ValueError:
            raise ValueError("O campo 'valor' deve ser um número válido.")


# ----------------------------
# Resposta de movimentação financeira
# ----------------------------
class FinanceiroResponse(FinanceiroBase):
    id: int  # ID da movimentação
    data_registro: datetime  # Data/hora da movimentação no modelo SQLAlchemy

    class Config:
        from_attributes = True  # Compatível com Pydantic v2, substitui orm_mode


# ----------------------------
# Resumo financeiro (entradas, saídas e saldo)
# ----------------------------
class ResumoFinanceiroResponse(BaseModel):
    total_entradas: float  # Soma das entradas
    total_saidas: float  # Soma das saídas
    saldo: float  # Saldo atual

    class Config:
        from_attributes = True  # Compatível com objetos ORM
