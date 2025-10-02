from pydantic import BaseModel, EmailStr  # BaseModel para schemas, EmailStr para validação de emails
from datetime import datetime  # Para campos de data/hora
from typing import Optional  # Para campos opcionais


# Classe base de Médico, usada para validação e herança
class MedicoBase(BaseModel):
    nome: str  # Nome completo do médico
    email: EmailStr  # Email do médico
    telefone: Optional[str] = None  # Telefone do médico (opcional)
    crm: str  # Número do CRM do médico
    especialidade: str  # Especialidade médica


# Schema usado para criar novos médicos (mesma estrutura do base)
class MedicoCreate(MedicoBase):
    pass  # Sem campos adicionais


# Schema usado para atualizar informações de médico (campos opcionais)
class MedicoUpdate(BaseModel):
    nome: Optional[str] = None  # Nome pode ser alterado
    email: Optional[EmailStr] = None  # Email pode ser alterado
    telefone: Optional[str] = None  # Telefone pode ser alterado
    especialidade: Optional[str] = None  # Especialidade pode ser alterada
    ativo: Optional[bool] = None  # Status de ativo/inativo


# Schema usado para respostas de médico (inclui campos do banco)
class MedicoResponse(MedicoBase):
    id: int  # ID do médico no banco
    ativo: bool  # Status ativo ou inativo
    criado_em: datetime  # Data de criação do registro
    atualizado_em: datetime  # Data da última atualização do registro

    class Config:
        orm_mode = True  # Compatibilidade com objetos ORM (SQLAlchemy)
