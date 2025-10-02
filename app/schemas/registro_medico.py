from pydantic import BaseModel  # BaseModel para schemas
from datetime import datetime  # Para campos de data/hora


# Classe base de Prontuário Médico, usada para validação e herança
class ProntuarioMedicoBase(BaseModel):
    paciente_id: int  # ID do paciente vinculado ao prontuário
    medico_id: int  # ID do médico responsável pelo registro
    descricao: str  # Descrição do prontuário ou observações clínicas


# Schema usado para criar um novo prontuário médico
class ProntuarioMedicoCreate(ProntuarioMedicoBase):
    pass  # Mantém a mesma estrutura do base


# Schema usado para resposta de prontuário médico (inclui campos do banco)
class ProntuarioMedicoResponse(ProntuarioMedicoBase):
    id: int  # ID único do registro
    data_hora: datetime  # Data e hora de criação do prontuário

    class Config:
        orm_mode = True  # Compatibilidade com objetos ORM (SQLAlchemy)
