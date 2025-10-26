from pydantic import BaseModel  # BaseModel para criar schemas e validar dados
from datetime import datetime  # datetime para campos de data e hora
from typing import Optional  # Optional permite campos que podem ser None
from app.models.medical import StatusConsulta  # Enum com status da consulta


# ----------------------------
# Classe base de Consulta
# ----------------------------
class ConsultaBase(BaseModel):
    paciente_id: int  # ID do paciente vinculado à consulta, obrigatório
    medico_id: int  # ID do médico vinculado à consulta, obrigatório
    data_hora: datetime  # Data e hora agendada da consulta, obrigatório
    duracao_minutos: Optional[int] = 30  # Duração da consulta (minutos), padrão 30
    status: Optional[StatusConsulta] = StatusConsulta.AGENDADA  # Status inicial, padrão AGENDADA
    observacoes: Optional[str] = None  # Observações adicionais, opcional


# ----------------------------
# Schema para criação de consultas
# ----------------------------
class ConsultaCreate(ConsultaBase):
    pass  # Mantém mesma estrutura do ConsultaBase para inserção de dados


# ----------------------------
# Schema para resposta de consultas
# ----------------------------
class ConsultaResponse(ConsultaBase):
    id: int  # ID único da consulta no banco
    criado_em: datetime  # Data/hora de criação do registro
    atualizado_em: datetime  # Data/hora da última atualização do registro

    class Config:
        from_attributes = True  # Compatível com Pydantic v2, serializa objetos ORM corretamente
