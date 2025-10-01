from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.db import get_db_session
from app import models as m
from app.core import security
from app.schemas.teleconsultation import TeleconsultationCreate, TeleconsultationResponse
from app.schemas.prescription import PrescriptionCreate, PrescriptionResponse
from app.schemas.medical_record import MedicalRecordCreate, MedicalRecordResponse

router = APIRouter()


def get_current_user(current_user=Depends(security.get_current_user)):
    return current_user


# ----------------------------
# Teleconsultas
# ----------------------------
@router.post("/teleconsultations", response_model=TeleconsultationResponse, status_code=status.HTTP_201_CREATED)
def create_teleconsultation(
        data: TeleconsultationCreate,
        db: Session = Depends(get_db_session),
        current_user=Depends(get_current_user)
):
    if current_user.get("role") != "MEDICO":
        raise HTTPException(status_code=403, detail="Apenas MEDICO pode criar teleconsultas")

    tele = m.Teleconsultation(**data.dict())
    db.add(tele)
    db.commit()
    db.refresh(tele)
    return tele


@router.get("/teleconsultations", response_model=List[TeleconsultationResponse])
def list_teleconsultations(
        db: Session = Depends(get_db_session),
        current_user=Depends(get_current_user)
):
    if current_user.get("role") not in ["MEDICO", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Sem permissão")
    return db.query(m.Teleconsultation).all()


# ----------------------------
# Prescrições
# ----------------------------
@router.post("/prescriptions", response_model=PrescriptionResponse, status_code=status.HTTP_201_CREATED)
def create_prescription(
        data: PrescriptionCreate,
        db: Session = Depends(get_db_session),
        current_user=Depends(get_current_user)
):
    if current_user.get("role") not in ["MEDICO", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Sem permissão")

    presc = m.Prescription(**data.dict())
    presc.data_hora = datetime.utcnow()
    db.add(presc)
    db.commit()
    db.refresh(presc)
    return presc


@router.get("/prescriptions", response_model=List[PrescriptionResponse])
def list_prescriptions(
        db: Session = Depends(get_db_session),
        current_user=Depends(get_current_user)
):
    if current_user.get("role") not in ["MEDICO", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Sem permissão")
    return db.query(m.Prescription).all()


# ----------------------------
# Prontuários médicos
# ----------------------------
@router.post("/medicalrecords", response_model=MedicalRecordResponse, status_code=status.HTTP_201_CREATED)
def create_medical_record(
        data: MedicalRecordCreate,
        db: Session = Depends(get_db_session),
        current_user=Depends(get_current_user)
):
    if current_user.get("role") not in ["MEDICO", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Sem permissão")

    record = m.MedicalRecord(**data.dict())
    record.data_hora = datetime.utcnow()
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/medicalrecords", response_model=List[MedicalRecordResponse])
def list_medical_records(
        db: Session = Depends(get_db_session),
        current_user=Depends(get_current_user)
):
    if current_user.get("role") not in ["MEDICO", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Sem permissão")
    return db.query(m.MedicalRecord).all()
