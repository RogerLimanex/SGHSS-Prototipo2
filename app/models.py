# D:\ProjectSGHSS\app\models.py
from sqlalchemy import (  # Importa os tipos e funcionalidades principais do SQLAlchemy
    Column, Integer, String, Boolean, DateTime, Date, Text, ForeignKey, Enum, Float
)
from sqlalchemy.orm import relationship  # Permite definir relacionamentos entre tabelas
from datetime import datetime  # Usado para timestamps automáticos
from app.db import Base  # Importa a classe base declarativa do SQLAlchemy
import enum  # Usado para criar enums (valores fixos controlados)


# =========================================================
# ENUMs
# =========================================================
class StatusConsulta(str, enum.Enum):
    """Enum de status possíveis de uma consulta médica."""
    AGENDADA = "agendada"  # Consulta foi agendada
    CONFIRMADA = "confirmada"  # Consulta confirmada pelo médico/paciente
    REALIZADA = "realizada"  # Consulta concluída
    CANCELADA = "cancelada"  # Consulta cancelada


class PapelUsuario(str, enum.Enum):
    """Enum que define os papéis dos usuários do sistema."""
    ADMIN = "ADMIN"  # Administrador do sistema
    MEDICO = "MEDICO"  # Usuário médico
    PACIENTE = "PACIENTE"  # Usuário paciente


# =========================================================
# MODELOS PRINCIPAIS
# =========================================================
class Usuario(Base):
    """Representa um usuário do sistema (admin, médico ou paciente)."""
    __tablename__ = "usuarios"  # Nome da tabela no banco de dados

    id = Column(Integer, primary_key=True, index=True)  # Chave primária
    email = Column(String(100), unique=True, index=True, nullable=False)  # E-mail único
    hashed_password = Column(String(255), nullable=False)  # Senha criptografada
    papel = Column(Enum(PapelUsuario), default=PapelUsuario.PACIENTE, nullable=False)  # Tipo de usuário
    ativo = Column(Boolean, default=True)  # Define se o usuário está ativo
    criado_em = Column(DateTime, default=datetime.utcnow)  # Data de criação

    logs_auditoria = relationship("LogAuditoria", back_populates="usuario")  # Relacionamento com logs de auditoria


class Paciente(Base):
    """Dados cadastrais de pacientes."""
    __tablename__ = "pacientes"

    id = Column(Integer, primary_key=True, index=True)  # Identificador único
    nome = Column(String(100), nullable=False)  # Nome completo
    email = Column(String(100), unique=True, index=True)  # E-mail do paciente
    telefone = Column(String(20))  # Telefone de contato
    cpf = Column(String(14), unique=True, index=True)  # CPF com formatação (###.###.###-##)
    data_nascimento = Column(Date)  # Data de nascimento
    endereco = Column(Text)  # Endereço completo
    criado_em = Column(DateTime, default=datetime.utcnow)  # Data de criação
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # Última atualização

    consultas = relationship("Consulta", back_populates="paciente")  # Consultas relacionadas
    prontuarios = relationship("Prontuario", back_populates="paciente")  # Prontuários clínicos
    prescricoes = relationship("Receita", back_populates="paciente")  # Prescrições médicas


class Medico(Base):
    """Dados de cadastro de médicos."""
    __tablename__ = "medicos"

    id = Column(Integer, primary_key=True, index=True)  # Identificador único
    nome = Column(String(100), nullable=False)  # Nome completo do médico
    email = Column(String(100), unique=True, index=True)  # E-mail profissional
    telefone = Column(String(20))  # Telefone de contato
    crm = Column(String(20), unique=True, index=True)  # Número do CRM
    especialidade = Column(String(50))  # Área de atuação
    ativo = Column(Boolean, default=True)  # Define se o médico está ativo
    criado_em = Column(DateTime, default=datetime.utcnow)  # Data de criação
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # Última atualização

    consultas = relationship("Consulta", back_populates="medico")  # Consultas do médico
    prontuarios = relationship("Prontuario", back_populates="medico")  # Prontuários registrados pelo médico
    prescricoes = relationship("Receita", back_populates="medico")  # Prescrições emitidas pelo médico


class Consulta(Base):
    """Consultas médicas agendadas entre pacientes e médicos."""
    __tablename__ = "consultas"

    id = Column(Integer, primary_key=True, index=True)  # Identificador da consulta
    paciente_id = Column(Integer, ForeignKey("pacientes.id"), nullable=False)  # Chave estrangeira para paciente
    medico_id = Column(Integer, ForeignKey("medicos.id"), nullable=False)  # Chave estrangeira para médico
    data_hora = Column(DateTime, nullable=False)  # Data e hora da consulta
    duracao_minutos = Column(Integer, default=30)  # Duração padrão em minutos
    status = Column(Enum(StatusConsulta), default=StatusConsulta.AGENDADA, nullable=False)  # Status atual da consulta
    observacoes = Column(Text)  # Observações adicionais
    criado_em = Column(DateTime, default=datetime.utcnow)  # Data de criação
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # Última atualização

    paciente = relationship("Paciente", back_populates="consultas")  # Relacionamento com paciente
    medico = relationship("Medico", back_populates="consultas")  # Relacionamento com médico
    teleconsultas = relationship("Teleconsulta", back_populates="consulta")  # Teleconsultas associadas


class Prontuario(Base):
    """Histórico clínico e registros de atendimento."""
    __tablename__ = "prontuarios"

    id = Column(Integer, primary_key=True, index=True)  # Identificador único
    paciente_id = Column(Integer, ForeignKey("pacientes.id"), nullable=False)  # Relaciona com paciente
    medico_id = Column(Integer, ForeignKey("medicos.id"), nullable=True)  # Relaciona com médico
    descricao = Column(Text, nullable=False)  # Descrição do registro clínico
    data_hora = Column(DateTime, nullable=True)  # Data do registro
    status = Column(String(20), default="ATIVO", nullable=True)  # Status do prontuário
    anexo = Column(Text, nullable=True)  # Caminho ou conteúdo de anexo (exames, PDFs, etc.)

    paciente = relationship("Paciente", back_populates="prontuarios")  # Ligação com paciente
    medico = relationship("Medico", back_populates="prontuarios")  # Ligação com médico

    def __repr__(self):  # Representação textual da classe (útil para debug/logs)
        return f"<Prontuario(id={self.id}, paciente_id={self.paciente_id}, medico_id={self.medico_id}, status={self.status})>"


class Receita(Base):
    """Prescrições médicas associadas a consultas."""
    __tablename__ = "prescricoes"

    id = Column(Integer, primary_key=True, index=True)  # Identificador único
    paciente_id = Column(Integer, ForeignKey("pacientes.id"), nullable=False)  # FK para paciente
    medico_id = Column(Integer, ForeignKey("medicos.id"), nullable=False)  # FK para médico
    medicamento = Column(String(255), nullable=False)  # Nome do medicamento
    dosagem = Column(String(100), nullable=False)  # Dosagem prescrita
    instrucoes = Column(Text)  # Instruções de uso
    data_hora = Column(DateTime, default=datetime.utcnow)  # Data da emissão
    status = Column(String(20), default="ATIVA")  # Status da prescrição (ATIVA/ENCERRADA)

    paciente = relationship("Paciente", back_populates="prescricoes")  # Ligação com paciente
    medico = relationship("Medico", back_populates="prescricoes")  # Ligação com médico


class Teleconsulta(Base):
    """Consultas médicas realizadas de forma remota (videoconferência)."""
    __tablename__ = "teleconsultas"

    id = Column(Integer, primary_key=True, index=True)  # Identificador único
    consulta_id = Column(Integer, ForeignKey("consultas.id"), nullable=False)  # FK para consulta associada
    link_video = Column(String(255))  # URL da videoconferência
    data_hora = Column(DateTime, default=datetime.utcnow)  # Data/hora da teleconsulta
    status = Column(Enum(StatusConsulta), default=StatusConsulta.AGENDADA, nullable=False)  # Status da teleconsulta

    consulta = relationship("Consulta", back_populates="teleconsultas")  # Ligação com consulta principal


class LogAuditoria(Base):
    """Registro de ações de usuários para fins de auditoria."""
    __tablename__ = "logs_auditoria"

    id = Column(Integer, primary_key=True, index=True)  # Identificador único
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))  # FK para o usuário que realizou a ação
    acao = Column(String(255), nullable=False)  # Descrição da ação (ex: "Login efetuado", "Consulta criada")
    timestamp = Column(DateTime, default=datetime.utcnow)  # Data e hora da ação

    usuario = relationship("Usuario", back_populates="logs_auditoria")  # Relacionamento inverso com usuário
