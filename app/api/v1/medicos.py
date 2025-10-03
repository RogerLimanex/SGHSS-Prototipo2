from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db import get_db_session
from app import models as m
from app.core import security
from app.schemas.medico import MedicoResponse

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
# Criar médico com campos separados
# ----------------------------
@roteador.post("/", response_model=MedicoResponse, status_code=status.HTTP_201_CREATED)
def criar_medico(
        nome: str = Form(...),
        email: str = Form(...),
        telefone: Optional[str] = Form(None),
        crm: str = Form(...),
        especialidade: Optional[str] = Form(None),
        db: Session = Depends(get_db_session),
        usuario_atual=Depends(obter_usuario_atual)
):
    if usuario_atual.get("role") != "ADMIN":
        raise HTTPException(status_code=403, detail="Apenas ADMIN pode criar médicos")

    if db.query(m.Medico).filter(m.Medico.email == email).first():
        raise HTTPException(status_code=400, detail="Email já cadastrado")
    if db.query(m.Medico).filter(m.Medico.crm == crm).first():
        raise HTTPException(status_code=400, detail="CRM já cadastrado")

    novo_medico = m.Medico(
        nome=nome,
        email=email,
        telefone=telefone,
        crm=crm,
        especialidade=especialidade
    )
    db.add(novo_medico)
    db.commit()
    db.refresh(novo_medico)
    return novo_medico


# ----------------------------
# Atualizar médico com campos separados
# ----------------------------
@roteador.put("/{medico_id}", response_model=MedicoResponse)
def atualizar_medico(
        medico_id: int,
        nome: Optional[str] = Form(None),
        email: Optional[str] = Form(None),
        telefone: Optional[str] = Form(None),
        crm: Optional[str] = Form(None),
        especialidade: Optional[str] = Form(None),
        db: Session = Depends(get_db_session),
        usuario_atual=Depends(obter_usuario_atual)
):
    if usuario_atual.get("role") != "ADMIN":
        raise HTTPException(status_code=403, detail="Apenas ADMIN pode atualizar médicos")

    db_medico = db.query(m.Medico).filter(m.Medico.id == medico_id).first()
    if not db_medico:
        raise HTTPException(status_code=404, detail="Médico não encontrado")

    if nome is not None:
        db_medico.nome = nome
    if email is not None:
        db_medico.email = email
    if telefone is not None:
        db_medico.telefone = telefone
    if crm is not None:
        db_medico.crm = crm
    if especialidade is not None:
        db_medico.especialidade = especialidade

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
