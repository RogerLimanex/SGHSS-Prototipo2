from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta

from app import models as m
from app.core import security
from app.db.session import get_db

router = APIRouter()
security_scheme = HTTPBearer()


# --------------------------
# Função para pegar usuário logado via token
# --------------------------
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Token ausente")
    token = credentials.credentials
    try:
        return security.decode_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido")


# --------------------------
# Funções auxiliares de parsing
# --------------------------
def parse_data_hora(data_consulta: str, hora_consulta: str) -> datetime:
    """Converte data_consulta e hora_consulta para datetime."""
    for sep in ("/", "-"):
        try:
            data_formatada = datetime.strptime(data_consulta, f"%d{sep}%m{sep}%Y")
            hora_formatada = datetime.strptime(hora_consulta, "%H:%M").time()
            return datetime.combine(data_formatada, hora_formatada)
        except ValueError:
            continue
    raise HTTPException(status_code=400, detail="Data ou hora inválida")


def format_data_hora(dt: datetime):
    """Retorna dict com data_consulta e hora_consulta"""
    return {
        "data_consulta": dt.strftime("%d/%m/%Y"),
        "hora_consulta": dt.strftime("%H:%M"),
    }


# --------------------------
# GET ALL - Listar consultas
# --------------------------
@router.get("/")
def listar_consultas(
        page: int = 1,
        size: int = 20,
        status_filter: Optional[str] = None,
        doctor_id: Optional[int] = None,
        patient_id: Optional[int] = None,
        current=Depends(get_current_user),
        db: Session = Depends(get_db),
):
    role = current.get("role")
    user_id = current.get("sub")

    query = db.query(m.Appointment)

    if role == "PATIENT":
        query = query.filter(m.Appointment.patient_id == user_id)
    if role == "PROFESSIONAL":
        query = query.filter(m.Appointment.doctor_id == user_id)

    if status_filter:
        try:
            status_enum = m.AppointmentStatus(status_filter.lower())
            query = query.filter(m.Appointment.status == status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail="Status inválido")

    if doctor_id:
        query = query.filter(m.Appointment.doctor_id == doctor_id)
    if patient_id:
        query = query.filter(m.Appointment.patient_id == patient_id)

    total = query.count()
    items = query.offset((page - 1) * size).limit(size).all()

    result = []
    for c in items:
        appt = {
            "id": c.id,
            "patient_id": c.patient_id,
            "doctor_id": c.doctor_id,
            **format_data_hora(c.data_hora),
            "duracao_minutos": c.duracao_minutos,
            "status": c.status.value,
            "observacoes": c.observacoes,
        }
        result.append(appt)

    return {"items": result, "total": total}


# --------------------------
# GET BY ID
# --------------------------
@router.get("/{appointment_id}")
def obter_consulta(
        appointment_id: int,
        current=Depends(get_current_user),
        db: Session = Depends(get_db),
):
    consulta = db.query(m.Appointment).filter(m.Appointment.id == appointment_id).first()
    if not consulta:
        raise HTTPException(status_code=404, detail="Consulta não encontrada")

    role = current.get("role")
    user_id = current.get("sub")

    if role == "PATIENT" and consulta.patient_id != user_id:
        raise HTTPException(status_code=403, detail="Sem permissão")
    if role == "PROFESSIONAL" and consulta.doctor_id != user_id:
        raise HTTPException(status_code=403, detail="Sem permissão")

    return {
        "id": consulta.id,
        "patient_id": consulta.patient_id,
        "doctor_id": consulta.doctor_id,
        **format_data_hora(consulta.data_hora),
        "duracao_minutos": consulta.duracao_minutos,
        "status": consulta.status.value,
        "observacoes": consulta.observacoes,
    }


# --------------------------
# CREATE
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
        db: Session = Depends(get_db),
):
    if current.get("role") not in ["ADMIN", "PROFESSIONAL"]:
        raise HTTPException(status_code=403, detail="Sem permissão para agendar consultas")

    data_hora = parse_data_hora(data_consulta, hora_consulta)

    paciente = db.query(m.Patient).filter(m.Patient.id == patient_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente não encontrado")

    medico = db.query(m.Doctor).filter(m.Doctor.id == doctor_id, m.Doctor.active == True).first()
    if not medico:
        raise HTTPException(status_code=404, detail="Médico não encontrado ou inativo")

    fim = data_hora + timedelta(minutes=duracao_minutos)
    conflito = db.query(m.Appointment).filter(
        m.Appointment.doctor_id == doctor_id,
        m.Appointment.data_hora < fim,
        (m.Appointment.data_hora + m.Appointment.duracao_minutos * timedelta(minutes=1)) > data_hora,
        m.Appointment.status != m.AppointmentStatus.CANCELADA,
    ).first()
    if conflito:
        raise HTTPException(status_code=400, detail="Médico já possui consulta neste horário")

    consulta = m.Appointment(
        patient_id=patient_id,
        doctor_id=doctor_id,
        data_hora=data_hora,
        duracao_minutos=duracao_minutos,
        observacoes=observacoes,
        status=m.AppointmentStatus.AGENDADA,
    )

    db.add(consulta)
    db.commit()
    db.refresh(consulta)

    return {
        "id": consulta.id,
        "patient_id": consulta.patient_id,
        "doctor_id": consulta.doctor_id,
        **format_data_hora(consulta.data_hora),
        "duracao_minutos": consulta.duracao_minutos,
        "status": consulta.status.value,
        "observacoes": consulta.observacoes,
    }


# --------------------------
# UPDATE
# --------------------------
@router.put("/{appointment_id}")
def atualizar_consulta(
        appointment_id: int,
        data_consulta: Optional[str] = None,
        hora_consulta: Optional[str] = None,
        status_update: Optional[str] = None,
        observacoes: Optional[str] = None,
        current=Depends(get_current_user),
        db: Session = Depends(get_db),
):
    consulta = db.query(m.Appointment).filter(m.Appointment.id == appointment_id).first()
    if not consulta:
        raise HTTPException(status_code=404, detail="Consulta não encontrada")

    role = current.get("role")
    user_id = current.get("sub")

    if role == "PATIENT":
        raise HTTPException(status_code=403, detail="Pacientes não podem alterar consultas")
    if role == "PROFESSIONAL" and consulta.doctor_id != user_id:
        raise HTTPException(status_code=403, detail="Sem permissão")

    if status_update:
        try:
            consulta.status = m.AppointmentStatus(status_update.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail="Status inválido")

    if data_consulta and hora_consulta:
        consulta.data_hora = parse_data_hora(data_consulta, hora_consulta)

    if observacoes is not None:
        consulta.observacoes = observacoes

    db.commit()
    db.refresh(consulta)

    return {
        "id": consulta.id,
        "patient_id": consulta.patient_id,
        "doctor_id": consulta.doctor_id,
        **format_data_hora(consulta.data_hora),
        "duracao_minutos": consulta.duracao_minutos,
        "status": consulta.status.value,
        "observacoes": consulta.observacoes,
    }


# --------------------------
# DELETE (cancelar consulta)
# --------------------------
@router.delete("/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancelar_consulta(
        appointment_id: int,
        current=Depends(get_current_user),
        db: Session = Depends(get_db),
):
    consulta = db.query(m.Appointment).filter(m.Appointment.id == appointment_id).first()
    if not consulta:
        raise HTTPException(status_code=404, detail="Consulta não encontrada")

    role = current.get("role")
    user_id = current.get("sub")

    if role == "PATIENT" and consulta.patient_id != user_id:
        raise HTTPException(status_code=403, detail="Sem permissão")
    if role == "PROFESSIONAL" and consulta.doctor_id != user_id:
        raise HTTPException(status_code=403, detail="Sem permissão")

    consulta.status = m.AppointmentStatus.CANCELADA
    db.commit()
    return None
