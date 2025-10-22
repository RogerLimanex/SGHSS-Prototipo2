from pydantic import BaseModel
from typing import Optional


class LeitoBase(BaseModel):
    """
    Schema base para criação/atualização de Leito.
    """
    numero: str
    status: str
    paciente_id: Optional[int] = None


class LeitoResponse(BaseModel):
    """
    Schema para retorno de Leito, compatível com FastAPI.
    Inclui ID e campos opcionais de paciente.
    """
    id: int
    numero: str
    status: str
    paciente_id: Optional[int] = None

    # Futuramente, campos de data podem ser adicionados como string:
    # data_ocupacao: Optional[str] = None

    class Config:
        from_attributes = True
