from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.db import get_db_session
from app import models as m
from app.core import security
from app.schemas import TeleconsultaCreate, TeleconsultaResponse  # Corrigido para nomes em português

roteador = APIRouter()


# ----------------------------
# Dependência para obter o usuário atual
# ----------------------------
def obter_usuario_atual(current_user=Depends(security.get_current_user)):
    return current_user


# ----------------------------
# Listar teleconsultas
# ----------------------------
@roteador.get("/", response_model=List[TeleconsultaResponse])
def listar_teleconsultas(
        db: Session = Depends(get_db_session),
        usuario_atual=Depends(obter_usuario_atual)
):
    """
    Lista todas as teleconsultas. Apenas ADMIN ou MEDICO podem acessar.
    """
    if usuario_atual.get("role") not in ["MEDICO", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Sem permissão")
    return db.query(m.Teleconsulta).all()


# ----------------------------
# Criar teleconsulta
# ----------------------------
@roteador.post("/", response_model=TeleconsultaResponse, status_code=status.HTTP_201_CREATED)
def criar_teleconsulta(
        teleconsulta: TeleconsultaCreate,
        db: Session = Depends(get_db_session),
        usuario_atual=Depends(obter_usuario_atual)
):
    """
    Cria uma nova teleconsulta vinculada a uma consulta existente.
    Apenas ADMIN ou MEDICO podem criar.
    """
    if usuario_atual.get("role") not in ["MEDICO", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Sem permissão")

    nova_teleconsulta = m.Teleconsulta(
        consulta_id=teleconsulta.consulta_id,
        link_video=teleconsulta.link_video,
        data_hora=datetime.now(),
        status=m.StatusConsulta.AGENDADA
    )
    db.add(nova_teleconsulta)
    db.commit()
    db.refresh(nova_teleconsulta)
    return nova_teleconsulta


# ----------------------------
# Cancelar teleconsulta
# ----------------------------
@roteador.post("/{teleconsulta_id}/cancelar", response_model=TeleconsultaResponse)
def cancelar_teleconsulta(
        teleconsulta_id: int,
        db: Session = Depends(get_db_session),
        usuario_atual=Depends(obter_usuario_atual)
):
    """
    Cancela uma teleconsulta existente. Apenas ADMIN ou MEDICO podem cancelar.
    """
    if usuario_atual.get("role") not in ["MEDICO", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Sem permissão")

    teleconsulta = db.query(m.Teleconsulta).filter(m.Teleconsulta.id == teleconsulta_id).first()
    if not teleconsulta:
        raise HTTPException(status_code=404, detail="Teleconsulta não encontrada")

    teleconsulta.status = m.StatusConsulta.CANCELADA
    db.commit()
    db.refresh(teleconsulta)
    return teleconsulta
