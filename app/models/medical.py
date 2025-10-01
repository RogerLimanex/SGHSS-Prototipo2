# app/models/medical.py
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db import Base


# -------------------
# Teleconsultas
# -------------------
class Teleconsultation(Base):
    __tablename__ = "teleconsultations"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    data_hora = Column(DateTime, default=datetime.utcnow)
    observacoes = Column(Text)

    paciente = relationship("Patient")
    medico = relationship("Doctor")


# -------------------
# Prescrições
# -------------------
class Prescription(Base):
    __tablename__ = "prescriptions"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    teleconsultation_id = Column(Integer, ForeignKey("teleconsultations.id"), nullable=True)
    medicamento = Column(String(255))
    posologia = Column(String(255))
    observacoes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    paciente = relationship("Patient")
    medico = relationship("Doctor")
    teleconsultation = relationship("Teleconsultation")


# -------------------
# Prontuários
# -------------------
class MedicalRecord(Base):
    __tablename__ = "medical_records"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=True)
    descricao = Column(Text)
    data_hora = Column(DateTime, default=datetime.utcnow)

    paciente = relationship("Patient")
    medico = relationship("Doctor")


# -------------------
# Logs de auditoria
# -------------------
class Log(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(255))
    table_name = Column(String(255))
    record_id = Column(Integer)
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
