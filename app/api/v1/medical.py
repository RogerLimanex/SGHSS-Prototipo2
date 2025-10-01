from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.db import get_db_session
from app import models as m
from app.core import security
from app.schemas import (
    TeleconsultationCreate, TeleconsultationResponse,
    PrescriptionCreate, PrescriptionResponse,
    MedicalRecordCreate, MedicalRecordResponse,
    AppointmentCreate, AppointmentResponse
)

router = APIRouter()


# ----------------------------
# Consultas (Atendimentos presenciais ou online)
# ----------------------------
@router.post("/consultas", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
def criar_consulta(
        data: AppointmentCreate,
        db: Session = Depends(get_db_session),
        current_user=Depends(security.get_current_user)
):
    if current_user.get("role") not in ["MEDICO", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Sem permissão")

    consulta = m.Appointment(
        patient_id=data.patient_id,
        doctor_id=data.doctor_id,
        data_hora=data.data_hora,
        duracao_minutos=data.duracao_minutos,
        observacoes=data.observacoes,
        status=m.AppointmentStatus.AGENDADA
    )
    db.add(consulta)
    db.commit()
    db.refresh(consulta)
    return consulta


@router.get("/consultas", response_model=List[AppointmentResponse])
def listar_consultas(
        db: Session = Depends(get_db_session),
        current_user=Depends(security.get_current_user)
):
    if current_user.get("role") not in ["MEDICO", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Sem permissão")
    return db.query(m.Appointment).all()


@router.post("/consultas/{consulta_id}/cancelar", response_model=AppointmentResponse)
def cancelar_consulta(
        consulta_id: int,
        db: Session = Depends(get_db_session),
        current_user=Depends(security.get_current_user)
):
    if current_user.get("role") not in ["MEDICO", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Sem permissão")

    consulta = db.query(m.Appointment).filter(m.Appointment.id == consulta_id).first()
    if not consulta:
        raise HTTPException(status_code=404, detail="Consulta não encontrada")

    consulta.status = m.AppointmentStatus.CANCELADA
    db.commit()
    db.refresh(consulta)
    return consulta


# ----------------------------
# Teleconsultas
# ----------------------------
@router.post("/teleconsultas", response_model=TeleconsultationResponse, status_code=status.HTTP_201_CREATED)
def criar_teleconsulta(
        data: TeleconsultationCreate,
        db: Session = Depends(get_db_session),
        current_user=Depends(security.get_current_user)
):
    if current_user.get("role") not in ["MEDICO", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Sem permissão")

    tele = m.Teleconsultation(
        appointment_id=data.appointment_id,
        link_video=data.link_video,
        data_hora=datetime.now(),
        status=m.AppointmentStatus.AGENDADA
    )
    db.add(tele)
    db.commit()
    db.refresh(tele)
    return tele


@router.get("/teleconsultas", response_model=List[TeleconsultationResponse])
def listar_teleconsultas(
        db: Session = Depends(get_db_session),
        current_user=Depends(security.get_current_user)
):
    if current_user.get("role") not in ["MEDICO", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Sem permissão")
    return db.query(m.Teleconsultation).all()


@router.post("/teleconsultas/{teleconsulta_id}/cancelar", response_model=TeleconsultationResponse)
def cancelar_teleconsulta(
        teleconsulta_id: int,
        db: Session = Depends(get_db_session),
        current_user=Depends(security.get_current_user)
):
    if current_user.get("role") not in ["MEDICO", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Sem permissão")

    tele = db.query(m.Teleconsultation).filter(m.Teleconsultation.id == teleconsulta_id).first()
    if not tele:
        raise HTTPException(status_code=404, detail="Teleconsulta não encontrada")

    tele.status = m.AppointmentStatus.CANCELADA
    db.commit()
    db.refresh(tele)
    return tele


# ----------------------------
# Prescrições
# ----------------------------
@router.post("/prescricoes", response_model=PrescriptionResponse, status_code=status.HTTP_201_CREATED)
def criar_prescricao(
        data: PrescriptionCreate,
        db: Session = Depends(get_db_session),
        current_user=Depends(security.get_current_user)
):
    if current_user.get("role") not in ["MEDICO", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Sem permissão")

    presc = m.Prescription(
        patient_id=data.patient_id,
        doctor_id=data.doctor_id,
        medicamento=data.medicamento,
        dosagem=data.dosagem,
        instrucoes=data.instrucoes,
        data_hora=datetime.now()
    )
    db.add(presc)
    db.commit()
    db.refresh(presc)
    return presc


@router.get("/prescricoes", response_model=List[PrescriptionResponse])
def listar_prescricoes(
        db: Session = Depends(get_db_session),
        current_user=Depends(security.get_current_user)
):
    if current_user.get("role") not in ["MEDICO", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Sem permissão")
    return db.query(m.Prescription).all()


@router.post("/prescricoes/{prescricao_id}/cancelar", response_model=PrescriptionResponse)
def cancelar_prescricao(
        prescricao_id: int,
        db: Session = Depends(get_db_session),
        current_user=Depends(security.get_current_user)
):
    if current_user.get("role") not in ["MEDICO", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Sem permissão")

    presc = db.query(m.Prescription).filter(m.Prescription.id == prescricao_id).first()
    if not presc:
        raise HTTPException(status_code=404, detail="Prescrição não encontrada")

    # Não tem status, então podemos simplesmente deletar ou marcar como inválida
    db.delete(presc)
    db.commit()
    return presc


# ----------------------------
# Prontuários
# ----------------------------
@router.post("/prontuarios", response_model=MedicalRecordResponse, status_code=status.HTTP_201_CREATED)
def criar_prontuario(
        data: MedicalRecordCreate,
        db: Session = Depends(get_db_session),
        current_user=Depends(security.get_current_user)
):
    if current_user.get("role") not in ["MEDICO", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Sem permissão")

    record = m.MedicalRecord(
        patient_id=data.patient_id,
        doctor_id=data.doctor_id,
        descricao=data.descricao,
        data_hora=datetime.now()
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/prontuarios", response_model=List[MedicalRecordResponse])
def listar_prontuarios(
        db: Session = Depends(get_db_session),
        current_user=Depends(security.get_current_user)
):
    if current_user.get("role") not in ["MEDICO", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Sem permissão")
    return db.query(m.MedicalRecord).all()


@router.post("/prontuarios/{prontuario_id}/cancelar", response_model=MedicalRecordResponse)
def cancelar_prontuario(
        prontuario_id: int,
        db: Session = Depends(get_db_session),
        current_user=Depends(security.get_current_user)
):
    if current_user.get("role") not in ["MEDICO", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Sem permissão")

    record = db.query(m.MedicalRecord).filter(m.MedicalRecord.id == prontuario_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Prontuário não encontrado")

    db.delete(record)
    db.commit()
    return record
