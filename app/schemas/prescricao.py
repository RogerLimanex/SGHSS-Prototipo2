from pydantic import BaseModel  # BaseModel para validação e estruturação dos dados
from datetime import datetime  # Para campos de data/hora
from typing import Optional  # Permite campos opcionais


# ----------------------------
# Schema base de Prescrição
# ----------------------------
class PrescricaoBase(BaseModel):
    paciente_id: int  # ID do paciente, obrigatório
    medico_id: int  # ID do médico, obrigatório
    medicamento: str  # Nome do medicamento, obrigatório
    dosagem: str  # Dosagem do medicamento, obrigatório
    instrucoes: Optional[str] = None  # Instruções adicionais, opcional


# ----------------------------
# Schema para criação de prescrição
# ----------------------------
class PrescricaoCreate(PrescricaoBase):
    pass  # Mantém a mesma estrutura do PrescricaoBase


# ----------------------------
# Schema para resposta de prescrição
# ----------------------------
class PrescricaoResponse(PrescricaoBase):
    id: int  # ID único da prescrição
    data_hora: datetime  # Data/hora da criação da prescrição
    status: str  # Status atual da prescrição (ex: ATIVA, CANCELADA)

    class Config:
        from_attributes = True  # Compatível com objetos ORM (Pydantic v2)
