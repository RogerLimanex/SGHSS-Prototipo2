# D:\ProjectSGHSS\app\api\v1\pacientes.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db import get_db_session
from app import models as m
from app.core import security
from app.schemas.paciente import PacienteCreate, PacienteUpdate, PacienteResponse

roteador = APIRouter()


def obter_usuario_atual(current_user=Depends(security.get_current_user)):
    return current_user


# ----------------------------
# Listar pacientes
# ----------------------------
@roteador.get("/", response_model=List[PacienteResponse])
def listar_pacientes(
        page: int = 1,
        size: int = 20,
        db: Session = Depends(get_db_session),
        current_user=Depends(obter_usuario_atual)
):
    if current_user.get("role") not in ["ADMIN", "MEDICO"]:
        raise HTTPException(status_code=403, detail="Sem permissão")
    return db.query(m.Paciente).offset((page - 1) * size).limit(size).all()


# ----------------------------
# Obter paciente por ID
# ----------------------------
@roteador.get("/{paciente_id}", response_model=PacienteResponse)
def obter_paciente(paciente_id: int, db: Session = Depends(get_db_session), current_user=Depends(obter_usuario_atual)):
    if current_user.get("role") not in ["ADMIN", "MEDICO"]:
        raise HTTPException(status_code=403, detail="Sem permissão")
    paciente = db.query(m.Paciente).filter(m.Paciente.id == paciente_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente não encontrado")
    return paciente


# ----------------------------
# Criar paciente
# ----------------------------
@roteador.post("/", response_model=PacienteResponse, status_code=status.HTTP_201_CREATED)
def criar_paciente(paciente: PacienteCreate, db: Session = Depends(get_db_session),
                   current_user=Depends(obter_usuario_atual)):
    if current_user.get("role") not in ["ADMIN", "MEDICO"]:
        raise HTTPException(status_code=403, detail="Sem permissão")
    if db.query(m.Paciente).filter(m.Paciente.email == paciente.email).first():
        raise HTTPException(status_code=400, detail="Email já cadastrado")
    novo = m.Paciente(**paciente.dict())
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo


# ----------------------------
# Atualizar paciente
# ----------------------------
@roteador.put("/{paciente_id}", response_model=PacienteResponse)
def atualizar_paciente(paciente_id: int, paciente: PacienteUpdate, db: Session = Depends(get_db_session),
                       current_user=Depends(obter_usuario_atual)):
    if current_user.get("role") not in ["ADMIN", "MEDICO"]:
        raise HTTPException(status_code=403, detail="Sem permissão")
    db_paciente = db.query(m.Paciente).filter(m.Paciente.id == paciente_id).first()
    if not db_paciente:
        raise HTTPException(status_code=404, detail="Paciente não encontrado")
    for field, value in paciente.dict(exclude_unset=True).items():
        setattr(db_paciente, field, value)
    db.commit()
    db.refresh(db_paciente)
    return db_paciente


# ----------------------------
# Deletar paciente
# ----------------------------
@roteador.delete("/{paciente_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_paciente(paciente_id: int, db: Session = Depends(get_db_session),
                     current_user=Depends(obter_usuario_atual)):
    if current_user.get("role") != "ADMIN":
        raise HTTPException(status_code=403, detail="Apenas ADMIN pode excluir")
    db_paciente = db.query(m.Paciente).filter(m.Paciente.id == paciente_id).first()
    if not db_paciente:
        raise HTTPException(status_code=404, detail="Paciente não encontrado")
    db.delete(db_paciente)
    db.commit()
    return None
