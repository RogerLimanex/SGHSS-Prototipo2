from pydantic import BaseModel  # BaseModel para schemas
from datetime import datetime  # Para campos de data/hora
from typing import Optional  # Para campos opcionais


# Classe base de Prescrição, usada para validação e herança
class PrescricaoBase(BaseModel):
    paciente_id: int  # ID do paciente que receberá a prescrição
    medico_id: int  # ID do médico que prescreveu
    medicamento: str  # Nome do medicamento
    dosagem: str  # Dosagem do medicamento
    instrucoes: Optional[str] = None  # Instruções adicionais (opcional)


# Schema usado para criar uma nova prescrição
class PrescricaoCreate(PrescricaoBase):
    pass  # Mantém a mesma estrutura do base


# Schema usado para resposta de prescrição (inclui campos do banco)
class PrescricaoResponse(PrescricaoBase):
    id: int  # ID único da prescrição no banco
    data_hora: datetime  # Data e hora de criação da prescrição

    class Config:
        orm_mode = True  # Compatibilidade com objetos ORM (SQLAlchemy)
