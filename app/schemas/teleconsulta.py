from pydantic import BaseModel  # BaseModel para schemas
from datetime import datetime  # Para campos de data/hora
from typing import Optional  # Para campos opcionais
from app.models import StatusConsulta  # Enum de status de consulta


# Classe base de Teleconsulta, usada para validação e herança
class TeleconsultaBase(BaseModel):
    consulta_id: int  # ID da consulta vinculada à teleconsulta
    link_video: Optional[str] = None  # Link para videoconferência (opcional)
    data_hora: Optional[datetime] = None  # Data e hora da teleconsulta (opcional)
    status: Optional[StatusConsulta] = StatusConsulta.AGENDADA  # Status inicial


# Schema usado para criar uma nova teleconsulta
class TeleconsultaCreate(TeleconsultaBase):
    pass  # Mantém a mesma estrutura do base


# Schema usado para resposta de teleconsulta (inclui campos do banco)
class TeleconsultaResponse(TeleconsultaBase):
    id: int  # ID único da teleconsulta no banco

    class Config:
        orm_mode = True  # Compatibilidade com objetos ORM (SQLAlchemy)
