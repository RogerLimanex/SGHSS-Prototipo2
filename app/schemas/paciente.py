from pydantic import BaseModel, EmailStr  # BaseModel para criar schemas, EmailStr valida emails
from datetime import date, datetime  # date para datas de nascimento, datetime para registros
from typing import Optional  # Para campos que podem ser None


# ----------------------------
# Classe base de Paciente
# ----------------------------
class PacienteBase(BaseModel):
    nome: str  # Nome completo do paciente, obrigatório
    email: Optional[EmailStr] = None  # Email do paciente, agora opcional para evitar erro de validação
    telefone: Optional[str] = None  # Telefone opcional
    cpf: Optional[str] = None  # CPF do paciente, agora opcional para evitar erro de validação
    data_nascimento: Optional[date] = None  # Data de nascimento, opcional
    endereco: Optional[str] = None  # Endereço opcional


# ----------------------------
# Schema usado para criar paciente
# ----------------------------
class PacienteCreate(PacienteBase):
    pass  # Mantém a mesma estrutura do PacienteBase, usado para inserção


# ----------------------------
# Schema usado para atualizar paciente
# ----------------------------
class PacienteUpdate(BaseModel):
    nome: Optional[str] = None  # Atualização do nome, opcional
    email: Optional[EmailStr] = None  # Atualização do email, opcional
    telefone: Optional[str] = None  # Atualização do telefone, opcional
    endereco: Optional[str] = None  # Atualização do endereço, opcional


# ----------------------------
# Schema usado para resposta de paciente
# ----------------------------
class PacienteResponse(PacienteBase):
    id: int  # ID único do paciente no banco
    criado_em: datetime  # Data e hora de criação do registro
    atualizado_em: datetime  # Data e hora da última atualização

    class Config:
        from_attributes = True  # Compatível com Pydantic v2, permite criar schema a partir de objetos ORM
