from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from typing import Optional
from app.db import get_db_session
from app import models as m
from app.core import security

router = APIRouter()
security_scheme = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Token ausente")
    token = credentials.credentials
    try:
        return security.decode_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido")


# GET ALL - Listar médicos
@router.get("/")
def listar_medicos(
        page: int = 1,
        size: int = 20,
        especialidade: Optional[str] = None,
        active: Optional[bool] = None,
        current=Depends(get_current_user),
        db: Session = Depends(get_db_session),
):
    if current.get("role") not in ["ADMIN", "PROFESSIONAL"]:
        raise HTTPException(status_code=403, detail="Sem permissão")

    stmt = select(m.Doctor)

    if especialidade:
        stmt = stmt.where(m.Doctor.especialidade.ilike(f"%{especialidade}%"))  # type: ignore
    if active is not None:
        stmt = stmt.where(m.Doctor.active == active)  # type: ignore

    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    items = db.execute(stmt.offset((page - 1) * size).limit(size)).scalars().all()

    return {"items": items, "total": total}


# GET BY ID - Obter médico por ID
@router.get("/{doctor_id}")
def obter_medico(
        doctor_id: int,
        current=Depends(get_current_user),
        db: Session = Depends(get_db_session),
):
    if current.get("role") not in ["ADMIN", "PROFESSIONAL"]:
        raise HTTPException(status_code=403, detail="Sem permissão")

    stmt = select(m.Doctor).where(m.Doctor.id == doctor_id)  # type: ignore
    doctor = db.scalar(stmt)

    if not doctor:
        raise HTTPException(status_code=404, detail="Médico não encontrado")
    return doctor


# CREATE - Criar médico
@router.post("/", status_code=status.HTTP_201_CREATED)
def criar_medico(
        nome: str,
        email: str,
        crm: str,
        especialidade: str,
        telefone: Optional[str] = None,
        current=Depends(get_current_user),
        db: Session = Depends(get_db_session),
):
    if current.get("role") != "ADMIN":
        raise HTTPException(status_code=403, detail="Apenas administradores podem criar médicos")

    # Verificar se email ou CRM já existem
    stmt_email = select(m.Doctor).where(m.Doctor.email == email)  # type: ignore
    if db.scalar(stmt_email):
        raise HTTPException(status_code=400, detail="Email já cadastrado")

    stmt_crm = select(m.Doctor).where(m.Doctor.crm == crm)  # type: ignore
    if db.scalar(stmt_crm):
        raise HTTPException(status_code=400, detail="CRM já cadastrado")

    doctor = m.Doctor(
        nome=nome,
        email=email,
        crm=crm,
        especialidade=especialidade,
        telefone=telefone,
    )

    db.add(doctor)
    db.commit()
    db.refresh(doctor)
    return doctor


# UPDATE - Atualizar médico
@router.put("/{doctor_id}")
def atualizar_medico(
        doctor_id: int,
        nome: Optional[str] = None,
        email: Optional[str] = None,
        telefone: Optional[str] = None,
        especialidade: Optional[str] = None,
        active: Optional[bool] = None,
        current=Depends(get_current_user),
        db: Session = Depends(get_db_session),
):
    if current.get("role") != "ADMIN":
        raise HTTPException(status_code=403, detail="Apenas administradores podem atualizar médicos")

    stmt = select(m.Doctor).where(m.Doctor.id == doctor_id)  # type: ignore
    doctor = db.scalar(stmt)

    if not doctor:
        raise HTTPException(status_code=404, detail="Médico não encontrado")

    # Atualizar campos fornecidos
    if nome is not None:
        doctor.nome = nome
    if email is not None:
        doctor.email = email
    if telefone is not None:
        doctor.telefone = telefone
    if especialidade is not None:
        doctor.especialidade = especialidade
    if active is not None:
        doctor.active = active

    db.commit()
    db.refresh(doctor)
    return doctor


# DELETE - Deletar médico (soft delete)
@router.delete("/{doctor_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_medico(
        doctor_id: int,
        current=Depends(get_current_user),
        db: Session = Depends(get_db_session),
):
    if current.get("role") != "ADMIN":
        raise HTTPException(status_code=403, detail="Apenas administradores podem excluir médicos")

    stmt = select(m.Doctor).where(m.Doctor.id == doctor_id)  # type: ignore
    doctor = db.scalar(stmt)

    if not doctor:
        raise HTTPException(status_code=404, detail="Médico não encontrado")

    # Soft delete
    doctor.active = False
    db.commit()
    return None
