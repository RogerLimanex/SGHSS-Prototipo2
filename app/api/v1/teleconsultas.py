# D:\ProjectSGHSS\app\api\v1\teleconsultas.py
from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.db import get_db_session
from app import models as m
from app.core import security
from app.schemas import TeleconsultaResponse
from app.utils.logs import registrar_log

roteador = APIRouter()


# ----------------------------
# Dependência para obter o usuário atual
# ----------------------------
def obter_usuario_atual(current_user=Depends(security.get_current_user)):
    """Retorna o usuário autenticado com id, email e role."""
    return current_user


# ----------------------------
# Criar teleconsulta
# ----------------------------
@roteador.post(
    "/",
    response_model=TeleconsultaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar Teleconsulta",
    operation_id="criarTeleconsulta"
)
def criar_teleconsulta(
        consulta_id: int = Form(...),
        link_video: str = Form(...),
        db: Session = Depends(get_db_session),
        usuario_atual=Depends(obter_usuario_atual)
):
    """Cria uma nova teleconsulta vinculada a uma consulta existente."""
    if usuario_atual["role"] not in ["MEDICO", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Sem permissão")

    nova_teleconsulta = m.Teleconsulta(
        consulta_id=consulta_id,
        link_video=link_video,
        data_hora=datetime.now(),
        status=m.StatusConsulta.AGENDADA
    )
    db.add(nova_teleconsulta)
    db.commit()
    db.refresh(nova_teleconsulta)

    # Log da criação
    registrar_log(
        db=db,
        usuario_email=usuario_atual["email"],
        tabela="Teleconsulta",
        registro_id=nova_teleconsulta.id,
        acao="CREATE",
        descricao=f"Teleconsulta criada para consulta {consulta_id}"
    )

    return nova_teleconsulta


# ----------------------------
# Listar teleconsultas
# ----------------------------
@roteador.get(
    "/",
    response_model=List[TeleconsultaResponse],
    summary="Listar Teleconsultas",
    operation_id="listarTeleconsultas"
)
def listar_teleconsultas(
        db: Session = Depends(get_db_session),
        usuario_atual=Depends(obter_usuario_atual)
):
    """Lista todas as teleconsultas. Apenas ADMIN ou MEDICO podem acessar."""
    if usuario_atual["role"] not in ["MEDICO", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Sem permissão")

    teleconsultas = db.query(m.Teleconsulta).all()

    # Log da listagem
    registrar_log(
        db=db,
        usuario_email=usuario_atual["email"],
        tabela="Teleconsulta",
        registro_id=None,
        acao="READ",
        descricao="Listagem de teleconsultas realizada",
        detalhes=f"Usuário {usuario_atual['email']} consultou as teleconsultas"
    )

    return teleconsultas


# ----------------------------
# Cancelar teleconsulta
# ----------------------------
@roteador.patch(
    "/{teleconsulta_id}/cancelar",
    response_model=TeleconsultaResponse,
    summary="Cancelar Teleconsulta",
    operation_id="cancelarTeleconsulta"
)
def cancelar_teleconsulta(
        teleconsulta_id: int,
        db: Session = Depends(get_db_session),
        usuario_atual=Depends(obter_usuario_atual)
):
    """Cancela uma teleconsulta existente (soft delete)."""
    if usuario_atual["role"] not in ["MEDICO", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Sem permissão")

    teleconsulta = db.query(m.Teleconsulta).filter(m.Teleconsulta.id == teleconsulta_id).first()
    if not teleconsulta:
        raise HTTPException(status_code=404, detail="Teleconsulta não encontrada")

    teleconsulta.status = m.StatusConsulta.CANCELADA
    db.commit()
    db.refresh(teleconsulta)

    # Log do cancelamento
    registrar_log(
        db=db,
        usuario_email=usuario_atual["email"],
        tabela="Teleconsulta",
        registro_id=teleconsulta.id,
        acao="DELETE",
        descricao=f"Teleconsulta {teleconsulta_id} cancelada pelo usuário"
    )

    return teleconsulta
