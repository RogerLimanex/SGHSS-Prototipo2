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

roteador = APIRouter()


# ----------------------------
# Consultas (Atendimentos presenciais ou online)
# ----------------------------
@roteador.post("/consultas", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
def criar_consulta(
        paciente_id: int,
        medico_id: int,
        data_hora: datetime,
        duracao_minutos: int = 30,
        observacoes: Optional[str] = None,
        db: Session = Depends(get_db_session),
        current_user=Depends(security.get_current_user)
):
    if current_user.get("role") not in ["MEDICO", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Sem permissão")

    consulta = m.Consulta(
        paciente_id=paciente_id,
        medico_id=medico_id,
        data_hora=data_hora,
        duracao_minutos=duracao_minutos,
        observacoes=observacoes,
        status=m.StatusConsulta.AGENDADA
    )
    db.add(consulta)
    db.commit()
    db.refresh(consulta)
    return consulta


@roteador.get("/consultas", response_model=List[AppointmentResponse])
def listar_consultas(
        db: Session = Depends(get_db_session),
        current_user=Depends(security.get_current_user)
):
    if current_user.get("role") not in ["MEDICO", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Sem permissão")
    return db.query(m.Consulta).all()


@roteador.post("/consultas/{consulta_id}/cancelar", response_model=AppointmentResponse)
def cancelar_consulta(
        consulta_id: int,
        db: Session = Depends(get_db_session),
        current_user=Depends(security.get_current_user)
):
    if current_user.get("role") not in ["MEDICO", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Sem permissão")

    consulta = db.query(m.Consulta).filter(m.Consulta.id == consulta_id).first()
    if not consulta:
        raise HTTPException(status_code=404, detail="Consulta não encontrada")

    consulta.status = m.StatusConsulta.CANCELADA
    db.commit()
    db.refresh(consulta)
    return consulta


# ----------------------------
# Teleconsultas
# ----------------------------
@roteador.post("/teleconsultas", response_model=TeleconsultationResponse, status_code=status.HTTP_201_CREATED)
def criar_teleconsulta(
        consulta_id: int,
        link_video: Optional[str] = None,
        db: Session = Depends(get_db_session),
        current_user=Depends(security.get_current_user)
):
    if current_user.get("role") not in ["MEDICO", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Sem permissão")

    tele = m.Teleconsulta(
        consulta_id=consulta_id,
        link_video=link_video,
        data_hora=datetime.now(),
        status=m.StatusConsulta.AGENDADA
    )
    db.add(tele)
    db.commit()
    db.refresh(tele)
    return tele


@roteador.get("/teleconsultas", response_model=List[TeleconsultationResponse])
def listar_teleconsultas(
        db: Session = Depends(get_db_session),
        current_user=Depends(security.get_current_user)
):
    if current_user.get("role") not in ["MEDICO", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Sem permissão")
    return db.query(m.Teleconsulta).all()


@roteador.post("/teleconsultas/{teleconsulta_id}/cancelar", response_model=TeleconsultationResponse)
def cancelar_teleconsulta(
        teleconsulta_id: int,
        db: Session = Depends(get_db_session),
        current_user=Depends(security.get_current_user)
):
    if current_user.get("role") not in ["MEDICO", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Sem permissão")

    tele = db.query(m.Teleconsulta).filter(m.Teleconsulta.id == teleconsulta_id).first()
    if not tele:
        raise HTTPException(status_code=404, detail="Teleconsulta não encontrada")

    tele.status = m.StatusConsulta.CANCELADA
    db.commit()
    db.refresh(tele)
    return tele


# ----------------------------
# Prescrições
# ----------------------------
@roteador.post("/prescricoes", response_model=PrescriptionResponse, status_code=status.HTTP_201_CREATED)
def criar_prescricao(
        paciente_id: int,
        medico_id: int,
        medicamento: str,
        dosagem: str,
        instrucoes: Optional[str] = None,
        db: Session = Depends(get_db_session),
        current_user=Depends(security.get_current_user)
):
    if current_user.get("role") not in ["MEDICO", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Sem permissão")

    presc = m.Receita(
        paciente_id=paciente_id,
        medico_id=medico_id,
        medicamento=medicamento,
        dosagem=dosagem,
        instrucoes=instrucoes,
        data_hora=datetime.now()
    )
    db.add(presc)
    db.commit()
    db.refresh(presc)
    return presc


@roteador.get("/prescricoes", response_model=List[PrescriptionResponse])
def listar_prescricoes(
        db: Session = Depends(get_db_session),
        current_user=Depends(security.get_current_user)
):
    if current_user.get("role") not in ["MEDICO", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Sem permissão")
    return db.query(m.Receita).all()


@roteador.post("/prescricoes/{prescricao_id}/cancelar", response_model=PrescriptionResponse)
def cancelar_prescricao(
        prescricao_id: int,
        db: Session = Depends(get_db_session),
        current_user=Depends(security.get_current_user)
):
    if current_user.get("role") not in ["MEDICO", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Sem permissão")

    presc = db.query(m.Receita).filter(m.Receita.id == prescricao_id).first()
    if not presc:
        raise HTTPException(status_code=404, detail="Prescrição não encontrada")

    db.delete(presc)
    db.commit()
    return presc


# ----------------------------
# Prontuários
# ----------------------------
@roteador.post("/prontuarios", response_model=MedicalRecordResponse, status_code=status.HTTP_201_CREATED)
def criar_prontuario(
        paciente_id: int,
        medico_id: int,
        descricao: str,
        db: Session = Depends(get_db_session),
        current_user=Depends(security.get_current_user)
):
    if current_user.get("role") not in ["MEDICO", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Sem permissão")

    record = m.Prontuario(
        paciente_id=paciente_id,
        medico_id=medico_id,
        descricao=descricao,
        data_hora=datetime.now()
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@roteador.get("/prontuarios", response_model=List[MedicalRecordResponse])
def listar_prontuarios(
        db: Session = Depends(get_db_session),
        current_user=Depends(security.get_current_user)
):
    if current_user.get("role") not in ["MEDICO", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Sem permissão")
    return db.query(m.Prontuario).all()


@roteador.post("/prontuarios/{prontuario_id}/cancelar", response_model=MedicalRecordResponse)
def cancelar_prontuario(
        prontuario_id: int,
        db: Session = Depends(get_db_session),
        current_user=Depends(security.get_current_user)
):
    if current_user.get("role") not in ["MEDICO", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Sem permissão")

    record = db.query(m.Prontuario).filter(m.Prontuario.id == prontuario_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Prontuário não encontrado")

    db.delete(record)
    db.commit()
    return record
