# app/models.py

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Date, Time, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.db import Base


class AppointmentStatus(str, enum.Enum):
    AGENDADA = "agendada"
    CONFIRMADA = "confirmada"
    REALIZADA = "realizada"
    CANCELADA = "cancelada"


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)

    # Separar data e hora corretamente
    data_consulta = Column(Date, nullable=False)
    hora_consulta = Column(Time, nullable=False)

    duracao_minutos = Column(Integer, default=30)
    status = Column(Enum(AppointmentStatus), default=AppointmentStatus.AGENDADA, nullable=False)
    observacoes = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamentos
    paciente = relationship("Patient")
    medico = relationship("Doctor", back_populates="consultas")
