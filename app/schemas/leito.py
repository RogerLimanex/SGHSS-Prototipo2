from pydantic import BaseModel  # BaseModel para criar schemas Pydantic
from typing import Optional  # Optional permite campos que podem ser None


# ----------------------------
# Schema base para Leito
# ----------------------------
class LeitoBase(BaseModel):
    """
    Schema base para criação/atualização de Leito.
    Contém apenas os campos essenciais que podem ser enviados via API.
    """
    numero: str  # Número do leito (obrigatório)
    status: str  # Status do leito (ex: LIVRE, OCUPADO)
    paciente_id: Optional[int] = None  # ID do paciente associado (opcional)


# ----------------------------
# Schema de resposta de Leito
# ----------------------------
class LeitoResponse(BaseModel):
    """
    Schema usado para retornar informações de um Leito via API.
    Inclui ID do registro e dados opcionais de paciente.
    """
    id: int  # ID único do leito
    numero: str  # Número do leito
    status: str  # Status do leito
    paciente_id: Optional[int] = None  # ID do paciente associado (opcional)

    # Futuramente, pode incluir campos de data, ex:
    # data_ocupacao: Optional[str] = None

    class Config:
        from_attributes = True  # Compatível com objetos ORM do SQLAlchemy
