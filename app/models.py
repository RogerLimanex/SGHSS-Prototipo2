# app/models.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Date, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime, date, time
import enum
from app.db import Base


# class AppointmentStatus(str, enum.Enum):
#     AGENDADA = "agendada"
#     CONFIRMADA = "confirmada"
#     REALIZADA = "realizada"
#     CANCELADA = "cancelada"
#
#
# class Appointment(Base):
#     __tablename__ = "appointments"
#
#     id = Column(Integer, primary_key=True, index=True)
#     patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
#     doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
#
#     # Separar data e hora
#     data_consulta = Column(Date, nullable=False)
#     hora_consulta = Column(DateTime,
#                            nullable=False)  # Pode ser Time ou DateTime, vou manter DateTime para facilitar queries
#
#     duracao_minutos = Column(Integer, default=30)
#     status = Column(Enum(AppointmentStatus), default=AppointmentStatus.AGENDADA, nullable=False)
#     observacoes = Column(Text)
#     created_at = Column(DateTime, default=datetime.utcnow)
#     updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
#
#     paciente = relationship("Patient")
#     medico = relationship("Doctor", back_populates="consultas")


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default='USER')
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Patient(Base):
    __tablename__ = "patients"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True)
    telefone = Column(String(20))
    cpf = Column(String(14), unique=True, index=True)
    data_nascimento = Column(Date)
    endereco = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Doctor(Base):
    __tablename__ = "doctors"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True)
    telefone = Column(String(20))
    crm = Column(String(20), unique=True, index=True)
    especialidade = Column(String(50))
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    consultas = relationship("Appointment", back_populates="medico")
