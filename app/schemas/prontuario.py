from pydantic import BaseModel  # BaseModel para validação e estruturação de dados
from datetime import datetime  # Para campos de data/hora
from typing import Optional  # Permite campos opcionais


# ----------------------------
# Schema base de Prontuário Médico
# ----------------------------
class ProntuarioMedicoBase(BaseModel):
    paciente_id: int  # ID do paciente vinculado ao prontuário
    medico_id: int  # ID do médico responsável pelo prontuário
    descricao: str  # Descrição do prontuário, obrigatório


# ----------------------------
# Schema para criar um novo prontuário médico
# ----------------------------
class ProntuarioMedicoCreate(ProntuarioMedicoBase):
    pass  # Mantém a mesma estrutura do ProntuarioMedicoBase para inserção


# ----------------------------
# Schema para resposta de prontuário médico
# ----------------------------
class ProntuarioMedicoResponse(ProntuarioMedicoBase):
    id: int  # ID único do prontuário no banco
    data_hora: datetime  # Data/hora de criação do prontuário
    anexo: Optional[str] = None  # Campo opcional para anexos ou links de arquivo

    class Config:
        from_attributes = True  # Compatível com objetos ORM (Pydantic v2)
