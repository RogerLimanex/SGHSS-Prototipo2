from pydantic import BaseModel, EmailStr  # BaseModel para criar schemas, EmailStr valida emails
from datetime import datetime  # Para campos de data/hora
from typing import Optional  # Permite campos opcionais


# ----------------------------
# Schema base de Médico
# ----------------------------
class MedicoBase(BaseModel):
    nome: str  # Nome completo do médico, obrigatório
    email: Optional[EmailStr] = None  # Email do médico, opcional para evitar erros de validação
    telefone: Optional[str] = None  # Telefone do médico, opcional
    crm: str  # Número do CRM do médico, obrigatório
    especialidade: Optional[str] = None  # Especialidade médica, opcional


# ----------------------------
# Schema para criação de médico
# ----------------------------
class MedicoCreate(MedicoBase):
    pass  # Mantém a mesma estrutura de MedicoBase


# ----------------------------
# Schema para atualização de médico
# ----------------------------
class MedicoUpdate(BaseModel):
    nome: Optional[str] = None  # Nome pode ser alterado
    email: Optional[EmailStr] = None  # Email pode ser alterado
    telefone: Optional[str] = None  # Telefone pode ser alterado
    especialidade: Optional[str] = None  # Especialidade pode ser alterada
    ativo: Optional[bool] = None  # Status ativo/inativo


# ----------------------------
# Schema de resposta de médico
# ----------------------------
class MedicoResponse(MedicoBase):
    id: int  # ID único do médico no banco
    ativo: bool  # Status ativo/inativo
    criado_em: datetime  # Data/hora de criação do registro
    atualizado_em: datetime  # Data/hora da última atualização

    class Config:
        from_attributes = True  # Compatível com objetos ORM (Pydantic v2)
