# D:\ProjectSGHSS\app\schemas\teleconsulta.py
from pydantic import BaseModel  # BaseModel do Pydantic para criar schemas de validação
from datetime import datetime  # Para campos de data e hora
from typing import Optional  # Para campos opcionais
from app.models.medical import StatusConsulta  # Enum de status de consulta (AGENDADA, CONFIRMADA, REALIZADA, CANCELADA)


# ----------------------------
# Schema base para Teleconsulta
# ----------------------------
class TeleconsultaBase(BaseModel):
    consulta_id: int  # ID da consulta vinculada à teleconsulta, obrigatório
    link_video: Optional[str] = None  # Link para videoconferência, opcional
    data_hora: Optional[datetime] = None  # Data e hora da teleconsulta, opcional
    status: Optional[StatusConsulta] = StatusConsulta.AGENDADA  # Status inicial, padrão AGENDADA


# ----------------------------
# Schema para criação de Teleconsulta
# ----------------------------
class TeleconsultaCreate(TeleconsultaBase):
    pass  # Mantém mesma estrutura do base, usado na inserção


# ----------------------------
# Schema de resposta de Teleconsulta
# ----------------------------
class TeleconsultaResponse(TeleconsultaBase):
    id: int  # ID único da teleconsulta no banco

    class Config:
        from_attributes = True  # Pydantic v2: compatível com objetos ORM, substitui orm_mode
