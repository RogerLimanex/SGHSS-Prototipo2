# D:\ProjectSGHSS\app\api\v1\medicos.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db import get_db_session
from app import models as m
from app.core import security
from app.schemas.medico import MedicoCreate, MedicoUpdate, MedicoResponse

roteador = APIRouter()


def obter_usuario_atual(current_user=Depends(security.get_current_user)):
    """Dependência simples para recuperar o usuário atual"""
    return current_user


# ----------------------------
# Listar médicos
# ----------------------------
@roteador.get("/", response_model=List[MedicoResponse])
def listar_medicos(
        pagina: int = 1,
        tamanho: int = 20,
        db: Session = Depends(get_db_session),
        usuario_atual=Depends(obter_usuario_atual)
):
    if usuario_atual.get("role") not in ["ADMIN", "MEDICO"]:
        raise HTTPException(status_code=403, detail="Sem permissão")
    return db.query(m.Medico).offset((pagina - 1) * tamanho).limit(tamanho).all()


# ----------------------------
# Obter médico por ID
# ----------------------------
@roteador.get("/{medico_id}", response_model=MedicoResponse)
def obter_medico(
        medico_id: int,
        db: Session = Depends(get_db_session),
        usuario_atual=Depends(obter_usuario_atual)
):
    if usuario_atual.get("role") not in ["ADMIN", "MEDICO"]:
        raise HTTPException(status_code=403, detail="Sem permissão")
    medico = db.query(m.Medico).filter(m.Medico.id == medico_id).first()
    if not medico:
        raise HTTPException(status_code=404, detail="Médico não encontrado")
    return medico


# ----------------------------
# Criar médico
# ----------------------------
@roteador.post("/", response_model=MedicoResponse, status_code=status.HTTP_201_CREATED)
def criar_medico(
        medico: MedicoCreate,
        db: Session = Depends(get_db_session),
        usuario_atual=Depends(obter_usuario_atual)
):
    if usuario_atual.get("role") != "ADMIN":
        raise HTTPException(status_code=403, detail="Apenas ADMIN pode criar médicos")
    if db.query(m.Medico).filter(m.Medico.email == medico.email).first():
        raise HTTPException(status_code=400, detail="Email já cadastrado")
    if db.query(m.Medico).filter(m.Medico.crm == medico.crm).first():
        raise HTTPException(status_code=400, detail="CRM já cadastrado")

    novo_medico = m.Medico(**medico.dict())
    db.add(novo_medico)
    db.commit()
    db.refresh(novo_medico)
    return novo_medico


# ----------------------------
# Atualizar médico
# ----------------------------
@roteador.put("/{medico_id}", response_model=MedicoResponse)
def atualizar_medico(
        medico_id: int,
        medico: MedicoUpdate,
        db: Session = Depends(get_db_session),
        usuario_atual=Depends(obter_usuario_atual)
):
    if usuario_atual.get("role") != "ADMIN":
        raise HTTPException(status_code=403, detail="Apenas ADMIN pode atualizar médicos")

    db_medico = db.query(m.Medico).filter(m.Medico.id == medico_id).first()
    if not db_medico:
        raise HTTPException(status_code=404, detail="Médico não encontrado")

    for campo, valor in medico.dict(exclude_unset=True).items():
        setattr(db_medico, campo, valor)

    db.commit()
    db.refresh(db_medico)
    return db_medico


# ----------------------------
# Deletar médico (soft-delete)
# ----------------------------
@roteador.delete("/{medico_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_medico(
        medico_id: int,
        db: Session = Depends(get_db_session),
        usuario_atual=Depends(obter_usuario_atual)
):
    if usuario_atual.get("role") != "ADMIN":
        raise HTTPException(status_code=403, detail="Apenas ADMIN pode excluir médicos")

    db_medico = db.query(m.Medico).filter(m.Medico.id == medico_id).first()
    if not db_medico:
        raise HTTPException(status_code=404, detail="Médico não encontrado")

    db_medico.ativo = False  # Soft delete
    db.commit()
    return None
