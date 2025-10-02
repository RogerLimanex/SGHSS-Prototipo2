from pydantic import BaseModel, EmailStr  # BaseModel e EmailStr para validação
from datetime import date, datetime  # date para data de nascimento, datetime para registros
from typing import Optional  # Para campos opcionais


# Classe base de Paciente, usada para validação e herança
class PacienteBase(BaseModel):
    nome: str  # Nome completo do paciente
    email: EmailStr  # Email do paciente
    telefone: Optional[str] = None  # Telefone opcional
    cpf: str  # CPF do paciente
    data_nascimento: date  # Data de nascimento
    endereco: Optional[str] = None  # Endereço opcional


# Schema usado para criar um novo paciente
class PacienteCreate(PacienteBase):
    pass  # Mantém a mesma estrutura do base


# Schema usado para atualizar dados do paciente
class PacienteUpdate(BaseModel):
    nome: Optional[str] = None
    email: Optional[EmailStr] = None
    telefone: Optional[str] = None
    endereco: Optional[str] = None


# Schema usado para resposta de paciente (inclui campos do banco)
class PacienteResponse(PacienteBase):
    id: int  # ID único do paciente no banco
    criado_em: datetime  # Data e hora de criação do registro
    atualizado_em: datetime  # Data e hora da última atualização

    class Config:
        orm_mode = True  # Compatibilidade com objetos ORM (SQLAlchemy)
