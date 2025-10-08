from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date, Text, ForeignKey, Enum
)
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.db import Base  # declarative_base do projeto


# -------------------
# ENUMs
# -------------------
class StatusConsulta(str, enum.Enum):
    AGENDADA = "agendada"
    CONFIRMADA = "confirmada"
    REALIZADA = "realizada"
    CANCELADA = "cancelada"


class PapelUsuario(str, enum.Enum):
    ADMIN = "ADMIN"
    MEDICO = "MEDICO"
    PACIENTE = "PACIENTE"


# -------------------
# MODELOS
# -------------------
class Usuario(Base):
    __tablename__ = "usuarios"  # tabela em português

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    papel = Column(Enum(PapelUsuario), default=PapelUsuario.PACIENTE, nullable=False)
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime, default=datetime.utcnow)

    # Relacionamento com logs (relação um-para-muitos)
    logs_auditoria = relationship("LogAuditoria", back_populates="usuario")


class Paciente(Base):
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


class Medico(Base):
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
    __tablename__ = "prontuarios"

    id = Column(Integer, primary_key=True, index=True)
    paciente_id = Column(Integer, ForeignKey("pacientes.id"), nullable=False)
    medico_id = Column(Integer, ForeignKey("medicos.id"), nullable=True)
    descricao = Column(Text, nullable=False)
    data_hora = Column(DateTime, default=datetime.utcnow)

    # Relacionamentos
    paciente = relationship("Paciente", back_populates="prontuarios")
    medico = relationship("Medico", back_populates="prontuarios")


class Receita(Base):
    __tablename__ = "prescricoes"

    id = Column(Integer, primary_key=True, index=True)
    paciente_id = Column(Integer, ForeignKey("pacientes.id"), nullable=False)
    medico_id = Column(Integer, ForeignKey("medicos.id"), nullable=False)
    medicamento = Column(String(255), nullable=False)
    dosagem = Column(String(100), nullable=False)
    instrucoes = Column(Text)
    data_hora = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default="ATIVA")  # ✅ adicionar esta linha

    # Relacionamentos
    paciente = relationship("Paciente", back_populates="prescricoes")
    medico = relationship("Medico", back_populates="prescricoes")


class Teleconsulta(Base):
    __tablename__ = "teleconsultas"

    id = Column(Integer, primary_key=True, index=True)
    consulta_id = Column(Integer, ForeignKey("consultas.id"), nullable=False)
    link_video = Column(String(255))
    data_hora = Column(DateTime, default=datetime.utcnow)
    status = Column(Enum(StatusConsulta), default=StatusConsulta.AGENDADA, nullable=False)

    # Relacionamentos
    consulta = relationship("Consulta", back_populates="teleconsultas")


class LogAuditoria(Base):
    __tablename__ = "logs_auditoria"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    acao = Column(String(255), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relacionamento
    usuario = relationship("Usuario", back_populates="logs_auditoria")
