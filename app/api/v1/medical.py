from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.db import get_db_session
from app import models as m
from app.core import security
from app.schemas import (
    TeleconsultationResponse,
    PrescriptionResponse,
    MedicalRecordResponse,
    AppointmentResponse
)

router = APIRouter()


# ----------------------------
# Consultas (Atendimentos presenciais ou online)
# ----------------------------
@router.post("/consultas", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
def criar_consulta(
        patient_id: int,
        doctor_id: int,
        data_hora: datetime,
        duracao_minutos: int = 30,
        observacoes: Optional[str] = None,
        db: Session = Depends(get_db_session),
        current_user=Depends(security.get_current_user)
):
    if current_user.get("role") not in ["MEDICO", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Sem permissão")

    consulta = m.Appointment(
        patient_id=patient_id,
        doctor_id=doctor_id,
        data_hora=data_hora,
        duracao_minutos=duracao_minutos,
        observacoes=observacoes,
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
        appointment_id: int,
        link_video: Optional[str] = None,
        db: Session = Depends(get_db_session),
        current_user=Depends(security.get_current_user)
):
    if current_user.get("role") not in ["MEDICO", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Sem permissão")

    tele = m.Teleconsultation(
        appointment_id=appointment_id,
        link_video=link_video,
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
        patient_id: int,
        doctor_id: int,
        medicamento: str,
        dosagem: str,
        instrucoes: Optional[str] = None,
        db: Session = Depends(get_db_session),
        current_user=Depends(security.get_current_user)
):
    if current_user.get("role") not in ["MEDICO", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Sem permissão")

    presc = m.Prescription(
        patient_id=patient_id,
        doctor_id=doctor_id,
        medicamento=medicamento,
        dosagem=dosagem,
        instrucoes=instrucoes,
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

    db.delete(presc)
    db.commit()
    return presc


# ----------------------------
# Prontuários
# ----------------------------
@router.post("/prontuarios", response_model=MedicalRecordResponse, status_code=status.HTTP_201_CREATED)
def criar_prontuario(
        patient_id: int,
        doctor_id: int,
        descricao: str,
        db: Session = Depends(get_db_session),
        current_user=Depends(security.get_current_user)
):
    if current_user.get("role") not in ["MEDICO", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Sem permissão")

    record = m.MedicalRecord(
        patient_id=patient_id,
        doctor_id=doctor_id,
        descricao=descricao,
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
