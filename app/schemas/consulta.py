from pydantic import BaseModel  # Importa o BaseModel do Pydantic para validar/estruturar os dados
from datetime import datetime  # Importa o tipo datetime para datas e horas
from typing import Optional  # Importa Optional para permitir campos opcionais
from app.models import StatusConsulta  # Importa o Enum de status de consulta do models


# Classe base de Consulta, usada para validação e herança
class ConsultaBase(BaseModel):
    paciente_id: int  # ID do paciente vinculado à consulta
    medico_id: int  # ID do médico vinculado à consulta
    data_hora: datetime  # Data e hora agendada da consulta
    duracao_minutos: Optional[int] = 30  # Duração da consulta em minutos (padrão: 30)
    status: Optional[StatusConsulta] = StatusConsulta.AGENDADA  # Status inicial da consulta
    observacoes: Optional[str] = None  # Campo opcional para observações adicionais


# Schema usado para criação de consultas (mesma estrutura do base)
class ConsultaCreate(ConsultaBase):
    pass  # Nenhuma modificação adicional em relação ao ConsultaBase


# Schema usado para resposta de consultas (inclui campos adicionais do banco)
class ConsultaResponse(ConsultaBase):
    id: int  # ID único da consulta no banco
    criado_em: datetime  # Data e hora de criação do registro
    atualizado_em: datetime  # Data e hora da última atualização do registro

    class Config:
        orm_mode = True  # Permite compatibilidade com objetos ORM (SQLAlchemy)
