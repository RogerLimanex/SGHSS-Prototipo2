from pydantic import BaseModel  # BaseModel do Pydantic para criar schemas de validação
from datetime import datetime  # Para campos de data e hora


# ----------------------------
# Classe base de Prontuário Médico
# ----------------------------
class ProntuarioMedicoBase(BaseModel):
    paciente_id: int  # ID do paciente vinculado ao prontuário, obrigatório
    medico_id: int  # ID do médico responsável pelo registro, obrigatório
    descricao: str  # Descrição ou observações clínicas, obrigatório


# ----------------------------
# Schema para criar um novo prontuário médico
# ----------------------------
class ProntuarioMedicoCreate(ProntuarioMedicoBase):
    pass  # Mantém a mesma estrutura do base, sem alterações adicionais


# ----------------------------
# Schema para resposta de prontuário médico
# ----------------------------
class ProntuarioMedicoResponse(ProntuarioMedicoBase):
    id: int  # ID único do registro no banco
    data_hora: datetime  # Data e hora de criação do registro

    class Config:
        from_attributes = True  # Pydantic v2: permite compatibilidade com objetos ORM (substitui orm_mode)
