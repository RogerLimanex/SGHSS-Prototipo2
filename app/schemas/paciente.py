from pydantic import BaseModel, EmailStr  # BaseModel para schemas, EmailStr valida emails
from datetime import date, datetime  # date para nascimento, datetime para registros
from typing import Optional  # Para campos que podem ser None


# ----------------------------
# Schema base de Paciente
# ----------------------------
class PacienteBase(BaseModel):
    nome: str  # Nome completo do paciente, obrigatório
    email: Optional[EmailStr] = None  # Email opcional
    telefone: Optional[str] = None  # Telefone opcional
    cpf: Optional[str] = None  # CPF opcional
    data_nascimento: Optional[date] = None  # Data de nascimento opcional
    endereco: Optional[str] = None  # Endereço opcional


# ----------------------------
# Schema para criação de paciente
# ----------------------------
class PacienteCreate(PacienteBase):
    pass  # Mantém a estrutura de PacienteBase


# ----------------------------
# Schema para atualização de paciente
# ----------------------------
class PacienteUpdate(BaseModel):
    nome: Optional[str] = None  # Atualização do nome
    email: Optional[EmailStr] = None  # Atualização do email
    telefone: Optional[str] = None  # Atualização do telefone
    endereco: Optional[str] = None  # Atualização do endereço


# ----------------------------
# Schema de resposta de paciente
# ----------------------------
class PacienteResponse(PacienteBase):
    id: int  # ID único do paciente
    criado_em: datetime  # Data/hora de criação do registro
    atualizado_em: datetime  # Data/hora da última atualização

    class Config:
        from_attributes = True  # Compatível com ORM (Pydantic v2)
