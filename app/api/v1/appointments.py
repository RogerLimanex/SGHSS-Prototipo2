from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta, time, date

from app.db import get_db_session
from app import models as m
from app.core import security

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
# Funções auxiliares
# --------------------------
def parse_data(data_consulta: str) -> date:
    """Converte data no formato dd/mm/yyyy ou yyyy-mm-dd para date"""
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(data_consulta, fmt).date()
        except ValueError:
            continue
    raise HTTPException(status_code=400, detail="Data inválida")


def parse_hora(hora_consulta: str) -> time:
    """Converte hora no formato HH:MM"""
    try:
        return datetime.strptime(hora_consulta, "%H:%M").time()
    except ValueError:
        raise HTTPException(status_code=400, detail="Hora inválida")


def combine_data_hora(data: date, hora: time) -> datetime:
    """Combina data e hora em um datetime"""
    return datetime.combine(data, hora)


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
        db: Session = Depends(get_db_session)
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
        # Extrai data e hora do campo data_hora
        data_formatada = c.data_hora.strftime("%d/%m/%Y")
        hora_formatada = c.data_hora.strftime("%H:%M")

        appt = {
            "id": c.id,
            "patient_id": c.patient_id,
            "doctor_id": c.doctor_id,
            "data_consulta": data_formatada,
            "hora_consulta": hora_formatada,
            "duracao_minutos": c.duracao_minutos,
            "status": c.status.value,
            "observacoes": c.observacoes
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
        db: Session = Depends(get_db_session)
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

    # Extrai data e hora do campo data_hora
    data_formatada = consulta.data_hora.strftime("%d/%m/%Y")
    hora_formatada = consulta.data_hora.strftime("%H:%M")

    return {
        "id": consulta.id,
        "patient_id": consulta.patient_id,
        "doctor_id": consulta.doctor_id,
        "data_consulta": data_formatada,
        "hora_consulta": hora_formatada,
        "duracao_minutos": consulta.duracao_minutos,
        "status": consulta.status.value,
        "observacoes": consulta.observacoes
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
        db: Session = Depends(get_db_session)
):
    if current.get("role") not in ["ADMIN", "PROFESSIONAL"]:
        raise HTTPException(status_code=403, detail="Sem permissão para agendar consultas")

    data_obj = parse_data(data_consulta)
    hora_obj = parse_hora(hora_consulta)
    data_hora_obj = combine_data_hora(data_obj, hora_obj)

    paciente = db.query(m.Patient).filter(m.Patient.id == patient_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente não encontrado")

    medico = db.query(m.Doctor).filter(m.Doctor.id == doctor_id, m.Doctor.active == True).first()
    if not medico:
        raise HTTPException(status_code=404, detail="Médico não encontrado ou inativo")

    # Verificar conflito
    inicio_nova = data_hora_obj
    fim_nova = inicio_nova + timedelta(minutes=duracao_minutos)

    consultas_existentes = db.query(m.Appointment).filter(
        m.Appointment.doctor_id == doctor_id,
        m.Appointment.status != m.AppointmentStatus.CANCELADA
    ).all()

    for c in consultas_existentes:
        inicio_existente = c.data_hora
        fim_existente = inicio_existente + timedelta(minutes=c.duracao_minutos)

        if inicio_nova < fim_existente and fim_nova > inicio_existente:
            raise HTTPException(status_code=400, detail="Médico já possui consulta neste horário")

    consulta = m.Appointment(
        patient_id=patient_id,
        doctor_id=doctor_id,
        data_hora=data_hora_obj,  # ← CORRIGIDO: usa data_hora
        duracao_minutos=duracao_minutos,
        observacoes=observacoes,
        status=m.AppointmentStatus.AGENDADA
    )

    db.add(consulta)
    db.commit()
    db.refresh(consulta)

    return {
        "id": consulta.id,
        "patient_id": consulta.patient_id,
        "doctor_id": consulta.doctor_id,
        "data_consulta": consulta.data_hora.strftime("%d/%m/%Y"),
        "hora_consulta": consulta.data_hora.strftime("%H:%M"),
        "duracao_minutos": consulta.duracao_minutos,
        "status": consulta.status.value,
        "observacoes": consulta.observacoes
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
        db: Session = Depends(get_db_session)
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
        data_obj = parse_data(data_consulta)
        hora_obj = parse_hora(hora_consulta)
        consulta.data_hora = combine_data_hora(data_obj, hora_obj)

    if observacoes is not None:
        consulta.observacoes = observacoes

    db.commit()
    db.refresh(consulta)

    return {
        "id": consulta.id,
        "patient_id": consulta.patient_id,
        "doctor_id": consulta.doctor_id,
        "data_consulta": consulta.data_hora.strftime("%d/%m/%Y"),
        "hora_consulta": consulta.data_hora.strftime("%H:%M"),
        "duracao_minutos": consulta.duracao_minutos,
        "status": consulta.status.value,
        "observacoes": consulta.observacoes
    }


# --------------------------
# DELETE (cancelar consulta)
# --------------------------
@router.delete("/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancelar_consulta(
        appointment_id: int,
        current=Depends(get_current_user),
        db: Session = Depends(get_db_session)
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
