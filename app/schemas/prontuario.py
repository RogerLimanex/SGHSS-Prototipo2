from pydantic import BaseModel
from datetime import datetime
from typing import Optional


# ----------------------------
# Classe base de Prontuário Médico
# ----------------------------
class ProntuarioMedicoBase(BaseModel):
    paciente_id: int
    medico_id: int
    descricao: str


# ----------------------------
# Schema para criar um novo prontuário médico
# ----------------------------
class ProntuarioMedicoCreate(ProntuarioMedicoBase):
    pass


# ----------------------------
# Schema para resposta de prontuário médico
# ----------------------------
class ProntuarioMedicoResponse(ProntuarioMedicoBase):
    id: int
    data_hora: datetime
    anexo: Optional[str] = None  # ✅ novo campo opcional para exibir o link do arquivo

    class Config:
        from_attributes = True  # compatível com objetos ORM
