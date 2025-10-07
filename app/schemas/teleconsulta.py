from pydantic import BaseModel  # BaseModel do Pydantic para criar schemas de validação
from datetime import datetime  # Para campos de data e hora
from typing import Optional  # Para campos opcionais
from app.models.medical import StatusConsulta  # Enum de status de consulta (AGENDADA, CONCLUIDA, CANCELADA)


# ----------------------------
# Classe base de Teleconsulta
# ----------------------------
class TeleconsultaBase(BaseModel):
    consulta_id: int  # ID da consulta vinculada à teleconsulta (obrigatório)
    link_video: Optional[str] = None  # Link para videoconferência (opcional)
    data_hora: Optional[datetime] = None  # Data e hora agendada da teleconsulta (opcional)
    status: Optional[StatusConsulta] = StatusConsulta.AGENDADA  # Status inicial (padrão: AGENDADA)


# ----------------------------
# Schema para criar uma nova teleconsulta
# ----------------------------
class TeleconsultaCreate(TeleconsultaBase):
    pass  # Mantém a mesma estrutura do base, sem alterações adicionais


# ----------------------------
# Schema para resposta de teleconsulta
# ----------------------------
class TeleconsultaResponse(TeleconsultaBase):
    id: int  # ID único da teleconsulta no banco

    class Config:
        from_attributes = True  # Pydantic v2: permite compatibilidade com objetos ORM (substitui orm_mode)
