# D:\ProjectSGHSS\app\models\medical.py
# Modelos principais do sistema: usuários, pacientes, médicos, consultas, prontuários, prescrições, teleconsultas
# Inclui enums para status e papéis

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date, Text, ForeignKey, Enum
)  # Colunas e tipos
from sqlalchemy.orm import relationship  # Para relacionamentos ORM
from datetime import datetime  # Datas e timestamps
import enum  # Para definir enums

from app.db import Base  # Base declarativa do projeto


# ============================================================
# ENUMs — Status de consultas, prescrições e papéis de usuário
# ============================================================

class StatusConsulta(str, enum.Enum):
    """Enum para status de uma consulta médica"""
    AGENDADA = "agendada"
    CONFIRMADA = "confirmada"
    REALIZADA = "realizada"
    CANCELADA = "cancelada"


class StatusPrescricao(str, enum.Enum):
    """Enum para status de prescrição médica"""
    ATIVA = "ATIVA"
    CANCELADA = "CANCELADA"


class PapelUsuario(str, enum.Enum):
    """Enum para papéis do sistema"""
    ADMIN = "ADMIN"
    MEDICO = "MEDICO"
    PACIENTE = "PACIENTE"


# ============================================================
# MODELOS PRINCIPAIS
# ============================================================

class Usuario(Base):
    """
    Usuário genérico (admin, médico ou paciente).
    Inclui email, senha hash, papel e status ativo.
    """
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    papel = Column(Enum(PapelUsuario), default=PapelUsuario.PACIENTE, nullable=False)
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime, default=datetime.utcnow)

    # Relacionamento com logs de auditoria
    logs_auditoria = relationship("LogAuditoria", back_populates="usuario")


class Paciente(Base):
    """
    Paciente cadastrado.
    Inclui dados pessoais, contatos e relacionamentos com consultas, prontuários, prescrições e leitos.
    """
    __tablename__ = "pacientes"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True)
    telefone = Column(String(20))
    cpf = Column(String(14), unique=True, index=True)
    data_nascimento = Column(Date)
    endereco = Column(Text)
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamentos
    consultas = relationship("Consulta", back_populates="paciente")
    prontuarios = relationship("Prontuario", back_populates="paciente")
    prescricoes = relationship("Receita", back_populates="paciente")
    leitos = relationship("Leito", back_populates="paciente", cascade="all, delete-orphan")


class Medico(Base):
    """
    Representa um médico cadastrado.
    Inclui CRM, especialidade, contatos e status ativo.
    """
    __tablename__ = "medicos"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True)
    telefone = Column(String(20))
    crm = Column(String(20), unique=True, index=True)
    especialidade = Column(String(50))
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamentos
    consultas = relationship("Consulta", back_populates="medico")
    prontuarios = relationship("Prontuario", back_populates="medico")
    prescricoes = relationship("Receita", back_populates="medico")


class Consulta(Base):
    """
    Consulta médica entre paciente e médico.
    Inclui data/hora, duração, status e observações.
    """
    __tablename__ = "consultas"

    id = Column(Integer, primary_key=True, index=True)
    paciente_id = Column(Integer, ForeignKey("pacientes.id"), nullable=False)
    medico_id = Column(Integer, ForeignKey("medicos.id"), nullable=False)
    data_hora = Column(DateTime, nullable=False)
    duracao_minutos = Column(Integer, default=30)
    status = Column(Enum(StatusConsulta), default=StatusConsulta.AGENDADA, nullable=False)
    observacoes = Column(Text)
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamentos
    paciente = relationship("Paciente", back_populates="consultas")
    medico = relationship("Medico", back_populates="consultas")
    teleconsultas = relationship("Teleconsulta", back_populates="consulta")


class Prontuario(Base):
    """
    Registro clínico de um paciente.
    Pode conter descrições, anexos e status.
    """
    __tablename__ = "prontuarios"

    id = Column(Integer, primary_key=True, index=True)
    paciente_id = Column(Integer, ForeignKey("pacientes.id"), nullable=False)
    medico_id = Column(Integer, ForeignKey("medicos.id"), nullable=True)
    descricao = Column(Text, nullable=False)
    anexo = Column(String(255), nullable=True)  # Arquivo opcional
    data_hora = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="ATIVO")

    # Relacionamentos
    paciente = relationship("Paciente", back_populates="prontuarios")
    medico = relationship("Medico", back_populates="prontuarios")


class Receita(Base):
    """
    Prescrição médica emitida por um médico a um paciente.
    Contém medicamento, dosagem, instruções e status.
    """
    __tablename__ = "prescricoes"

    id = Column(Integer, primary_key=True, index=True)
    paciente_id = Column(Integer, ForeignKey("pacientes.id"), nullable=False)
    medico_id = Column(Integer, ForeignKey("medicos.id"), nullable=False)
    medicamento = Column(String(255), nullable=False)
    dosagem = Column(String(100), nullable=False)
    instrucoes = Column(Text)
    data_hora = Column(DateTime, default=datetime.utcnow)
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = Column(String(20), default="ATIVA")

    # Relacionamentos
    paciente = relationship("Paciente", back_populates="prescricoes")
    medico = relationship("Medico", back_populates="prescricoes")


class Teleconsulta(Base):
    """
    Consulta médica realizada por videoconferência.
    Relacionada à consulta principal.
    """
    __tablename__ = "teleconsultas"

    id = Column(Integer, primary_key=True, index=True)
    consulta_id = Column(Integer, ForeignKey("consultas.id"), nullable=False)
    link_video = Column(String(255))
    data_hora = Column(DateTime, default=datetime.utcnow)
    status = Column(Enum(StatusConsulta), default=StatusConsulta.AGENDADA, nullable=False)

    # Relacionamento
    consulta = relationship("Consulta", back_populates="teleconsultas")


class LogAuditoria(Base):
    """
    Log de ações dos usuários para auditoria.
    """
    __tablename__ = "logs_auditoria"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    acao = Column(String(255), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relacionamento
    usuario = relationship("Usuario", back_populates="logs_auditoria")
