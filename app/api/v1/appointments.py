from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta

from app.db import get_db
from app.models import Appointment, Patient, Doctor, AppointmentStatus, AuditLog, UserRole
from app.core.security import get_current_user

router = APIRouter()


# --------------------------
# Função para converter data e hora
# --------------------------
def parse_data_hora(data_consulta: str, hora_consulta: str) -> datetime:
    for sep in ('/', '-'):
        try:
            data_formatada = datetime.strptime(data_consulta, f"%d{sep}%m{sep}%Y")
            hora_formatada = datetime.strptime(hora_consulta, "%H:%M").time()
            return datetime.combine(data_formatada, hora_formatada)
        except ValueError:
            continue
    raise HTTPException(status_code=400, detail="Data ou hora inválida")


def format_data_hora(dt: datetime):
    return {
        "data_consulta": dt.strftime("%d/%m/%Y"),
        "hora_consulta": dt.strftime("%H:%M")
    }


# --------------------------
# LISTAR CONSULTAS
# --------------------------
@router.get("/")
def listar_consultas(
        page: int = 1,
        size: int = 20,
        status_filter: Optional[str] = None,
        doctor_id: Optional[int] = None,
        patient_id: Optional[int] = None,
        current=Depends(get_current_user),
        db: Session = Depends(get_db)
):
    role = current.get("role")
    user_id = current.get("sub")

    query = db.query(Appointment)

    if role == UserRole.PATIENT.value:
        query = query.filter(Appointment.patient_id == user_id)
    elif role == UserRole.PROFESSIONAL.value:
        query = query.filter(Appointment.doctor_id == user_id)

    if status_filter:
        try:
            status_enum = AppointmentStatus(status_filter.lower())
            query = query.filter(Appointment.status == status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail="Status inválido")

    if doctor_id:
        query = query.filter(Appointment.doctor_id == doctor_id)
    if patient_id:
        query = query.filter(Appointment.patient_id == patient_id)

    total = query.count()
    items = query.offset((page - 1) * size).limit(size).all()

    result = []
    for c in items:
        result.append({
            "id": c.id,
            "patient_id": c.patient_id,
            "doctor_id": c.doctor_id,
            **format_data_hora(c.data_hora),
            "duracao_minutos": c.duracao_minutos,
            "status": c.status.value,
            "observacoes": c.observacoes
        })

    return {"items": result, "total": total}


# --------------------------
# OBTER CONSULTA POR ID
# --------------------------
@router.get("/{appointment_id}")
def obter_consulta(appointment_id: int, current=Depends(get_current_user), db: Session = Depends(get_db)):
    consulta = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not consulta:
        raise HTTPException(status_code=404, detail="Consulta não encontrada")

    role = current.get("role")
    user_id = current.get("sub")

    if role == UserRole.PATIENT.value and consulta.patient_id != user_id:
        raise HTTPException(status_code=403, detail="Sem permissão")
    if role == UserRole.PROFESSIONAL.value and consulta.doctor_id != user_id:
        raise HTTPException(status_code=403, detail="Sem permissão")

    return {
        "id": consulta.id,
        "patient_id": consulta.patient_id,
        "doctor_id": consulta.doctor_id,
        **format_data_hora(consulta.data_hora),
        "duracao_minutos": consulta.duracao_minutos,
        "status": consulta.status.value,
        "observacoes": consulta.observacoes
    }


# --------------------------
# CRIAR CONSULTA
# --------------------------
@router.post("/", status_code=status.HTTP_201_CREATED)
def criar_consulta(
        patient_id: int,
        doctor_id: int,
        data_consulta: str,
        hora_consulta: str,
        duracao_minutos: int = 30,
        observacoes: Optional[str] = None,
        current=Depends(get_current_user),
        db: Session = Depends(get_db)
):
    if current.get("role") not in [UserRole.ADMIN.value, UserRole.PROFESSIONAL.value]:
        raise HTTPException(status_code=403, detail="Sem permissão para agendar consultas")

    data_hora = parse_data_hora(data_consulta, hora_consulta)

    paciente = db.query(Patient).filter(Patient.id == patient_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente não encontrado")

    medico = db.query(Doctor).filter(Doctor.id == doctor_id, Doctor.active == True).first()
    if not medico:
        raise HTTPException(status_code=404, detail="Médico não encontrado ou inativo")

    fim = data_hora + timedelta(minutes=duracao_minutos)
    conflito = db.query(Appointment).filter(
        Appointment.doctor_id == doctor_id,
        Appointment.data_hora < fim,
        (Appointment.data_hora + timedelta(minutes=Appointment.duracao_minutos)) > data_hora,
        Appointment.status != AppointmentStatus.CANCELADA
    ).first()
    if conflito:
        raise HTTPException(status_code=400, detail="Médico já possui consulta neste horário")

    consulta = Appointment(
        patient_id=patient_id,
        doctor_id=doctor_id,
        data_hora=data_hora,
        duracao_minutos=duracao_minutos,
        observacoes=observacoes,
        status=AppointmentStatus.AGENDADA
    )

    db.add(consulta)
    db.commit()
    db.refresh(consulta)

    # Auditoria
    log = AuditLog(user_id=current.get("sub"), action="Criou consulta", table_name="appointments",
                   record_id=consulta.id)
    db.add(log)
    db.commit()

    return {
        "id": consulta.id,
        "patient_id": consulta.patient_id,
        "doctor_id": consulta.doctor_id,
        **format_data_hora(consulta.data_hora),
        "duracao_minutos": consulta.duracao_minutos,
        "status": consulta.status.value,
        "observacoes": consulta.observacoes
    }


# --------------------------
# ATUALIZAR CONSULTA
# --------------------------
@router.put("/{appointment_id}")
def atualizar_consulta(
        appointment_id: int,
        data_consulta: Optional[str] = None,
        hora_consulta: Optional[str] = None,
        status_update: Optional[str] = None,
        observacoes: Optional[str] = None,
        current=Depends(get_current_user),
        db: Session = Depends(get_db)
):
    consulta = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not consulta:
        raise HTTPException(status_code=404, detail="Consulta não encontrada")

    role = current.get("role")
    user_id = current.get("sub")

    if role == UserRole.PATIENT.value:
        raise HTTPException(status_code=403, detail="Pacientes não podem alterar consultas")

    if role == UserRole.PROFESSIONAL.value and consulta.doctor_id != user_id:
        raise HTTPException(status_code=403, detail="Sem permissão")

    if status_update:
        try:
            consulta.status = AppointmentStatus(status_update.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail="Status inválido")

    if data_consulta and hora_consulta:
        consulta.data_hora = parse_data_hora(data_consulta, hora_consulta)

    if observacoes is not None:
        consulta.observacoes = observacoes

    db.commit()
    db.refresh(consulta)

    # Auditoria
    log = AuditLog(user_id=current.get("sub"), action="Atualizou consulta", table_name="appointments",
                   record_id=consulta.id)
    db.add(log)
    db.commit()

    return {
        "id": consulta.id,
        "patient_id": consulta.patient_id,
        "doctor_id": consulta.doctor_id,
        **format_data_hora(consulta.data_hora),
        "duracao_minutos": consulta.duracao_minutos,
        "status": consulta.status.value,
        "observacoes": consulta.observacoes
    }


# --------------------------
# CANCELAR CONSULTA
# --------------------------
@router.delete("/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancelar_consulta(appointment_id: int, current=Depends(get_current_user), db: Session = Depends(get_db)):
    consulta = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not consulta:
        raise HTTPException(status_code=404, detail="Consulta não encontrada")

    role = current.get("role")
    user_id = current.get("sub")

    if role == UserRole.PATIENT.value and consulta.patient_id != user_id:
        raise HTTPException(status_code=403, detail="Sem permissão")
    if role == UserRole.PROFESSIONAL.value and consulta.doctor_id != user_id:
        raise HTTPException(status_code=403, detail="Sem permissão")

    consulta.status = AppointmentStatus.CANCELADA
    db.commit()

    # Auditoria
    log = AuditLog(user_id=current.get("sub"), action="Cancelou consulta", table_name="appointments",
                   record_id=consulta.id)
    db.add(log)
    db.commit()
    return None
