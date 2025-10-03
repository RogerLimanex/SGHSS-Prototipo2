from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.db import get_db_session
from app import models as m
from app.core import security
from app.schemas import ProntuarioMedicoResponse

roteador = APIRouter()


# ----------------------------
# Dependência para obter o usuário atual
# ----------------------------
def obter_usuario_atual(current_user=Depends(security.get_current_user)):
    return current_user


# ----------------------------
# Criar prontuário médico com campos separados
# ----------------------------
@roteador.post("/prontuarios", response_model=ProntuarioMedicoResponse, status_code=status.HTTP_201_CREATED)
def criar_prontuario(
        paciente_id: int = Form(...),
        medico_id: int = Form(...),
        descricao: str = Form(...),
        db: Session = Depends(get_db_session),
        usuario_atual=Depends(obter_usuario_atual)
):
    """
    Cria um novo prontuário médico para um paciente.
    Apenas ADMIN ou MEDICO podem criar.
    """
    if usuario_atual.get("role") not in ["MEDICO", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Sem permissão")

    novo_prontuario = m.Prontuario(
        paciente_id=paciente_id,
        medico_id=medico_id,
        descricao=descricao,
        data_hora=datetime.now(),
        status="ATIVO"  # Mantém status inicial como ATIVO
    )
    db.add(novo_prontuario)
    db.commit()
    db.refresh(novo_prontuario)
    return novo_prontuario


# ----------------------------
# Listar prontuários médicos
# ----------------------------
@roteador.get("/prontuarios", response_model=List[ProntuarioMedicoResponse])
def listar_prontuarios(
        db: Session = Depends(get_db_session),
        usuario_atual=Depends(obter_usuario_atual)
):
    """
    Lista todos os prontuários médicos cadastrados.
    Apenas ADMIN ou MEDICO podem visualizar.
    """
    if usuario_atual.get("role") not in ["MEDICO", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Sem permissão")

    return db.query(m.Prontuario).all()


# ----------------------------
# Cancelar prontuário médico
# ----------------------------
@roteador.post("/prontuarios/{prontuario_id}/cancelar", response_model=ProntuarioMedicoResponse)
def cancelar_prontuario(
        prontuario_id: int,
        db: Session = Depends(get_db_session),
        usuario_atual=Depends(obter_usuario_atual)
):
    """
    Cancela (inativa) um prontuário médico existente.
    Apenas ADMIN ou MEDICO podem cancelar.
    """
    if usuario_atual.get("role") not in ["MEDICO", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Sem permissão")

    prontuario = db.query(m.Prontuario).filter(m.Prontuario.id == prontuario_id).first()
    if not prontuario:
        raise HTTPException(status_code=404, detail="Prontuário não encontrado")

    prontuario.status = "CANCELADO"  # Marca como cancelado, sem excluir do banco
    db.commit()
    db.refresh(prontuario)
    return prontuario
