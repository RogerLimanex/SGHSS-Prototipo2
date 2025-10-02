from pydantic import BaseModel
from datetime import datetime
from typing import Optional


# ----------------------------
# Classe base de Prescrição
# ----------------------------
class PrescricaoBase(BaseModel):
    paciente_id: int  # ID do paciente que receberá a prescrição
    medico_id: int  # ID do médico que prescreveu
    medicamento: str  # Nome do medicamento
    dosagem: str  # Dosagem do medicamento
    instrucoes: Optional[str] = None  # Instruções adicionais (opcional)


# ----------------------------
# Schema usado para criar uma nova prescrição
# ----------------------------
class PrescricaoCreate(PrescricaoBase):
    pass  # Mantém a mesma estrutura do base


# ----------------------------
# Schema usado para resposta de prescrição
# ----------------------------
class PrescricaoResponse(PrescricaoBase):
    id: int  # ID único da prescrição no banco
    data_hora: datetime  # Data e hora de criação da prescrição
    status: str  # Status da prescrição (ex: ATIVA, CANCELADA)

    class Config:
        from_attributes = True  # Compatibilidade com objetos ORM (SQLAlchemy)
