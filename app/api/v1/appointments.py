# app/api/v1/appointments.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, time, date

from app.db import get_db_session
from app import models as m
from app.core import security
from pydantic import BaseModel

router = APIRouter()


# ----------------------------
# Schemas
# ----------------------------
class AppointmentBase(BaseModel):
    patient_id: int
    doctor_id: int
    data_consulta: date
    hora_consulta: time
    duracao_minutos: Optional[int] = 30
    observacoes: Optional[str] = None


class AppointmentCreate(AppointmentBase):
    pass


class AppointmentUpdate(BaseModel):
    data_consulta: Optional[date] = None
    hora_consulta: Optional[time] = None
    duracao_minutos: Optional[int] = None
    observacoes: Optional[str] = None
    status: Optional[m.AppointmentStatus] = None


class AppointmentResponse(AppointmentBase):
    id: int
    status: m.AppointmentStatus

    class Config:
        orm_mode = True


# ----------------------------
# Criar agendamento
# ----------------------------
@router.post("/", response_model=AppointmentResponse, status_code=201)
def create_appointment(
        appointment_in: AppointmentCreate,
        db: Session = Depends(get_db_session),
        current_user=Depends(security.get_current_user)
):
    # Apenas Admin ou Profissional podem criar
    if current_user.get("role") not in ["ADMIN", "PROFESSIONAL"]:
        raise HTTPException(status_code=403, detail="Sem permissão")

    # Verificar se paciente e médico existem
    patient = db.query(m.Patient).filter(m.Patient.id == appointment_in.patient_id).first()
    doctor = db.query(m.Doctor).filter(m.Doctor.id == appointment_in.doctor_id).first()
    if not patient or not doctor:
        raise HTTPException(status_code=404, detail="Paciente ou médico não encontrado")

    appointment = m.Appointment(
        patient_id=appointment_in.patient_id,
        doctor_id=appointment_in.doctor_id,
        data_consulta=appointment_in.data_consulta,
        hora_consulta=appointment_in.hora_consulta,
        duracao_minutos=appointment_in.duracao_minutos,
        observacoes=appointment_in.observacoes
    )

    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment


# ----------------------------
# Listar agendamentos do usuário
# ----------------------------
@router.get("/", response_model=List[AppointmentResponse])
def list_appointments(
        db: Session = Depends(get_db_session),
        current_user=Depends(security.get_current_user)
):
    # Admin vê todos, Profissional vê apenas consultas dele, paciente vê só as suas
    query = db.query(m.Appointment)
    role = current_user.get("role")
    user_id = int(current_user["sub"])

    if role == "PROFESSIONAL":
        # Encontrar id do doctor vinculado ao usuário
        doctor = db.query(m.Doctor).filter(m.Doctor.email == current_user.get("email")).first()
        if doctor:
            query = query.filter(m.Appointment.doctor_id == doctor.id)
        else:
            return []
    elif role == "USER":
        query = query.filter(m.Appointment.patient_id == user_id)

    return query.all()


# ----------------------------
# Atualizar agendamento
# ----------------------------
@router.put("/{appointment_id}", response_model=AppointmentResponse)
def update_appointment(
        appointment_id: int,
        appointment_in: AppointmentUpdate,
        db: Session = Depends(get_db_session),
        current_user=Depends(security.get_current_user)
):
    appointment = db.query(m.Appointment).filter(m.Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado")

    # Controle de perfil
    role = current_user.get("role")
    if role == "USER" and appointment.patient_id != int(current_user["sub"]):
        raise HTTPException(status_code=403, detail="Sem permissão")
    if role == "PROFESSIONAL":
        doctor = db.query(m.Doctor).filter(m.Doctor.email == current_user.get("email")).first()
        if not doctor or doctor.id != appointment.doctor_id:
            raise HTTPException(status_code=403, detail="Sem permissão")

    # Atualizar campos fornecidos
    for field, value in appointment_in.dict(exclude_unset=True).items():
        setattr(appointment, field, value)

    db.commit()
    db.refresh(appointment)
    return appointment


# ----------------------------
# Deletar agendamento
# ----------------------------
@router.delete("/{appointment_id}", status_code=204)
def delete_appointment(
        appointment_id: int,
        db: Session = Depends(get_db_session),
        current_user=Depends(security.get_current_user)
):
    appointment = db.query(m.Appointment).filter(m.Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado")

    role = current_user.get("role")
    if role == "USER" and appointment.patient_id != int(current_user["sub"]):
        raise HTTPException(status_code=403, detail="Sem permissão")
    if role == "PROFESSIONAL":
        doctor = db.query(m.Doctor).filter(m.Doctor.email == current_user.get("email")).first()
        if not doctor or doctor.id != appointment.doctor_id:
            raise HTTPException(status_code=403, detail="Sem permissão")

    db.delete(appointment)
    db.commit()
    return None
