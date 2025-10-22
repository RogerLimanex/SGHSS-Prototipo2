# D:\ProjectSGHSS\app\schemas\suprimento.py
from pydantic import BaseModel, validator
from datetime import date, datetime
from typing import Optional


class SuprimentoBase(BaseModel):
    """
    Schema base para criação e atualização de suprimentos.
    Define os campos esperados ao criar ou editar um suprimento.
    """
    nome: str
    quantidade: int
    data_validade: Optional[date] = None
    descricao: Optional[str] = None

    @validator("data_validade", pre=True)
    def converter_data_validade(cls, valor):
        """
        Converte a data informada como string no formato dd/mm/yyyy
        para um objeto datetime.date.
        Caso o campo venha vazio ou None, mantém como None.
        """
        if isinstance(valor, str):
            try:
                return datetime.strptime(valor, "%d/%m/%Y").date()
            except ValueError:
                raise ValueError("Formato de data inválido. Use dd/mm/yyyy.")
        return valor


class SuprimentoResponse(SuprimentoBase):
    """
    Schema de resposta retornado pela API.
    Inclui o ID do suprimento e permite leitura ORM.
    """
    id: int

    class Config:
        from_attributes = True
