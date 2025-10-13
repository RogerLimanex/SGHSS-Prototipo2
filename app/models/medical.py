from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date, Text, ForeignKey, Enum
)
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.db import Base  # declarative_base do projeto


# ============================================================
# ENUMs — Definem valores fixos para status e papéis do sistema
# ============================================================
class StatusConsulta(str, enum.Enum):
    """Enum para representar o status de uma consulta médica."""
    AGENDADA = "agendada"
    CONFIRMADA = "confirmada"
    REALIZADA = "realizada"
    CANCELADA = "cancelada"


class StatusPrescricao(str, enum.Enum):
    """Enum para representar o status de uma prescrição médica."""
    ATIVA = "ATIVA"
    CANCELADA = "CANCELADA"


class PapelUsuario(str, enum.Enum):
    """Enum que define os papéis dos usuários no sistema."""
    ADMIN = "ADMIN"
    MEDICO = "MEDICO"
    PACIENTE = "PACIENTE"


# ============================================================
# MODELOS PRINCIPAIS DO SISTEMA
# ============================================================

class Usuario(Base):
    """
    Representa um usuário genérico do sistema (admin, médico ou paciente).
    Inclui autenticação, papel e estado ativo/inativo.
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
    Representa um paciente cadastrado no sistema.
    Inclui dados pessoais, contato e relacionamentos com consultas,
    prontuários, prescrições e leitos.
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

    # 🔁 Novo relacionamento com o modelo Leito
    leitos = relationship("Leito", back_populates="paciente", cascade="all, delete-orphan")


class Medico(Base):
    """
    Representa um médico cadastrado.
    Contém CRM, especialidade e estado de atividade.
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
    Representa uma consulta médica agendada entre paciente e médico.
    Inclui data, duração, status e observações.
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
    Representa o registro clínico de um paciente.
    Pode conter descrições, anexos e status.
    """
    __tablename__ = "prontuarios"

    id = Column(Integer, primary_key=True, index=True)
    paciente_id = Column(Integer, ForeignKey("pacientes.id"), nullable=False)
    medico_id = Column(Integer, ForeignKey("medicos.id"), nullable=True)
    descricao = Column(Text, nullable=False)
    anexo = Column(String(255), nullable=True)  # Arquivo de apoio (opcional)
    data_hora = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="ATIVO")

    # Relacionamentos
    paciente = relationship("Paciente", back_populates="prontuarios")
    medico = relationship("Medico", back_populates="prontuarios")


class Receita(Base):
    """
    Representa uma prescrição médica emitida por um médico a um paciente.
    Inclui medicamento, dosagem, instruções e status.
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
    Representa uma consulta realizada por videoconferência.
    Relacionada diretamente à consulta principal.
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
    Registra ações dos usuários no sistema para fins de auditoria e segurança.
    """
    __tablename__ = "logs_auditoria"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    acao = Column(String(255), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relacionamento
    usuario = relationship("Usuario", back_populates="logs_auditoria")
