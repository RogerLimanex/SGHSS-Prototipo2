# app/api/v1/appointments.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from app.db import get_db_session
from app import models as m
from app.schemas.appointment import AppointmentCreate, AppointmentUpdate, AppointmentResponse
from app.core import security
from typing import List

router = APIRouter()


# LISTAR agendamentos
@router.get("/", response_model=List[AppointmentResponse])
def list_appointments(
        db: Session = Depends(get_db_session),
        current_user=Depends(security.get_current_user)
):
    role = current_user.get("role")
    user_id = int(current_user["sub"])

    if role == "ADMIN":
        appointments = db.query(m.Appointment).all()
    elif role == "PROFESSIONAL":
        appointments = db.query(m.Appointment).filter(m.Appointment.doctor_id == user_id).all()
    else:  # PATIENT
        appointments = db.query(m.Appointment).filter(m.Appointment.patient_id == user_id).all()

    return appointments


# CRIAR agendamento
@router.post("/", response_model=AppointmentResponse, status_code=201)
def create_appointment(
        appointment_in: AppointmentCreate,
        db: Session = Depends(get_db_session),
        current_user=Depends(security.get_current_user)
):
    role = current_user.get("role")
    user_id = int(current_user["sub"])

    # Patients só podem criar consultas para si mesmos
    if role == "PATIENT" and appointment_in.patient_id != user_id:
        raise HTTPException(status_code=403, detail="Paciente só pode criar suas próprias consultas")

    data_hora = datetime.combine(appointment_in.data_consulta, appointment_in.hora_consulta)
    appointment = m.Appointment(
        patient_id=appointment_in.patient_id,
        doctor_id=appointment_in.doctor_id,
        data_consulta=appointment_in.data_consulta,
        hora_consulta=data_hora,
        duracao_minutos=appointment_in.duracao_minutos,
        observacoes=appointment_in.observacoes
    )

    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment


# ATUALIZAR agendamento
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

    role = current_user.get("role")
    user_id = int(current_user["sub"])

    # Pacientes só podem atualizar suas próprias consultas
    if role == "PATIENT" and appointment.patient_id != user_id:
        raise HTTPException(status_code=403, detail="Paciente só pode atualizar suas próprias consultas")
    # Profissionais só podem atualizar consultas que são deles
    if role == "PROFESSIONAL" and appointment.doctor_id != user_id:
        raise HTTPException(status_code=403, detail="Profissional só pode atualizar suas próprias consultas")

    if appointment_in.data_consulta:
        appointment.data_consulta = appointment_in.data_consulta
    if appointment_in.hora_consulta:
        appointment.hora_consulta = datetime.combine(appointment_in.data_consulta or appointment.data_consulta,
                                                     appointment_in.hora_consulta)
    if appointment_in.duracao_minutos:
        appointment.duracao_minutos = appointment_in.duracao_minutos
    if appointment_in.observacoes is not None:
        appointment.observacoes = appointment_in.observacoes
    if appointment_in.status:
        # Apenas Admin ou Profissional podem alterar status
        if role not in ["ADMIN", "PROFESSIONAL"]:
            raise HTTPException(status_code=403, detail="Sem permissão para alterar status")
        appointment.status = appointment_in.status

    db.commit()
    db.refresh(appointment)
    return appointment


# EXCLUIR agendamento
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
    user_id = int(current_user["sub"])

    if role == "PATIENT" and appointment.patient_id != user_id:
        raise HTTPException(status_code=403, detail="Paciente só pode excluir suas próprias consultas")
    if role == "PROFESSIONAL" and appointment.doctor_id != user_id:
        raise HTTPException(status_code=403, detail="Profissional só pode excluir suas próprias consultas")

    db.delete(appointment)
    db.commit()
    return None
