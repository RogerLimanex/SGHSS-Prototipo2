from pydantic import BaseModel  # BaseModel para validação e estruturação dos dados
from datetime import datetime  # Para campos de data/hora
from typing import Optional  # Permite campos opcionais


# ----------------------------
# Classe base de Prescrição
# ----------------------------
class PrescricaoBase(BaseModel):
    paciente_id: int  # ID do paciente que receberá a prescrição, obrigatório
    medico_id: int  # ID do médico que prescreveu, obrigatório
    medicamento: str  # Nome do medicamento, obrigatório
    dosagem: str  # Dosagem do medicamento, obrigatório
    instrucoes: Optional[str] = None  # Instruções adicionais (opcional)


# ----------------------------
# Schema para criação de prescrição
# ----------------------------
class PrescricaoCreate(PrescricaoBase):
    pass  # Mantém a mesma estrutura do PrescricaoBase, sem alterações


# ----------------------------
# Schema para resposta de prescrição
# ----------------------------
class PrescricaoResponse(PrescricaoBase):
    id: int  # ID único da prescrição no banco
    data_hora: datetime  # Data e hora da criação da prescrição
    status: str  # Status da prescrição (ex: ATIVA, CANCELADA)

    class Config:
        from_attributes = True  # Pydantic v2: permite compatibilidade com objetos ORM (substitui orm_mode)
