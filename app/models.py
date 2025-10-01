from sqlalchemy import Column, Integer, String, DateTime, Boolean, Date, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base
import enum


# -------------------
# ENUM de Status
# -------------------
class AppointmentStatus(str, enum.Enum):
    AGENDADA = "agendada"
    CONFIRMADA = "confirmada"
    REALIZADA = "realizada"
    CANCELADA = "cancelada"


# -------------------
# User
# -------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default='USER')
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# -------------------
# Patient
# -------------------
class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=True)
    telefone = Column(String(20))
    cpf = Column(String(14), unique=True, index=True, nullable=True)
    data_nascimento = Column(Date)
    endereco = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# -------------------
# Doctor
# -------------------
class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=True)
    telefone = Column(String(20))
    crm = Column(String(20), unique=True, index=True, nullable=True)  # Registro profissional
    especialidade = Column(String(50))
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamento com consultas
    consultas = relationship("Appointment", back_populates="medico")


# -------------------
# Appointment
# -------------------
class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    data_hora = Column(DateTime, nullable=False)
    duracao_minutos = Column(Integer, default=30)
    status = Column(Enum(AppointmentStatus), default=AppointmentStatus.AGENDADA, nullable=False)
    observacoes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamentos
    paciente = relationship("Patient")
    medico = relationship("Doctor", back_populates="consultas")
