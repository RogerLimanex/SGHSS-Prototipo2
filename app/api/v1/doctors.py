from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db import get_db_session
from app import models as m
from app.core import security
from app.schemas.doctor import DoctorCreate, DoctorUpdate, DoctorResponse

router = APIRouter()


def get_current_user(current_user=Depends(security.get_current_user)):
    return current_user


# ----------------------------
# Listar médicos
# ----------------------------
@router.get("/", response_model=List[DoctorResponse])
def listar_medicos(
        page: int = 1,
        size: int = 20,
        db: Session = Depends(get_db_session),
        current_user=Depends(get_current_user)
):
    if current_user.get("role") not in ["ADMIN", "MEDICO"]:
        raise HTTPException(status_code=403, detail="Sem permissão")

    medicos = db.query(m.Doctor).offset((page - 1) * size).limit(size).all()
    return medicos


# ----------------------------
# Obter médico por ID
# ----------------------------
@router.get("/{doctor_id}", response_model=DoctorResponse)
def obter_medico(
        doctor_id: int,
        db: Session = Depends(get_db_session),
        current_user=Depends(get_current_user)
):
    if current_user.get("role") not in ["ADMIN", "MEDICO"]:
        raise HTTPException(status_code=403, detail="Sem permissão")

    medico = db.query(m.Doctor).filter(m.Doctor.id == doctor_id).first()
    if not medico:
        raise HTTPException(status_code=404, detail="Médico não encontrado")
    return medico


# ----------------------------
# Criar médico
# ----------------------------
@router.post("/", response_model=DoctorResponse, status_code=status.HTTP_201_CREATED)
def criar_medico(
        medico: DoctorCreate,
        db: Session = Depends(get_db_session),
        current_user=Depends(get_current_user)
):
    if current_user.get("role") != "ADMIN":
        raise HTTPException(status_code=403, detail="Apenas ADMIN pode criar médicos")

    if db.query(m.Doctor).filter(m.Doctor.email == medico.email).first():
        raise HTTPException(status_code=400, detail="Email já cadastrado")
    if db.query(m.Doctor).filter(m.Doctor.crm == medico.crm).first():
        raise HTTPException(status_code=400, detail="CRM já cadastrado")

    novo_medico = m.Doctor(**medico.dict())
    db.add(novo_medico)
    db.commit()
    db.refresh(novo_medico)
    return novo_medico


# ----------------------------
# Atualizar médico
# ----------------------------
@router.put("/{doctor_id}", response_model=DoctorResponse)
def atualizar_medico(
        doctor_id: int,
        medico: DoctorUpdate,
        db: Session = Depends(get_db_session),
        current_user=Depends(get_current_user)
):
    if current_user.get("role") != "ADMIN":
        raise HTTPException(status_code=403, detail="Apenas ADMIN pode atualizar médicos")

    db_medico = db.query(m.Doctor).filter(m.Doctor.id == doctor_id).first()
    if not db_medico:
        raise HTTPException(status_code=404, detail="Médico não encontrado")

    for field, value in medico.dict(exclude_unset=True).items():
        setattr(db_medico, field, value)

    db.commit()
    db.refresh(db_medico)
    return db_medico


# ----------------------------
# Deletar médico
# ----------------------------
@router.delete("/{doctor_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_medico(
        doctor_id: int,
        db: Session = Depends(get_db_session),
        current_user=Depends(get_current_user)
):
    if current_user.get("role") != "ADMIN":
        raise HTTPException(status_code=403, detail="Apenas ADMIN pode excluir médicos")

    db_medico = db.query(m.Doctor).filter(m.Doctor.id == doctor_id).first()
    if not db_medico:
        raise HTTPException(status_code=404, detail="Médico não encontrado")

    # Soft delete
    db_medico.active = False
    db.commit()
    return None
