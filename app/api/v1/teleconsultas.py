from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.db import get_db
from app import models as m
from app.core import security
from app.schemas import TeleconsultaResponse
from app.utils.logs import registrar_log

roteador = APIRouter()


# ============================================================
# FUNÇÃO AUXILIAR: Obter usuário atual
# ============================================================
def obter_usuario_atual(
        current_user=Depends(security.get_current_user),
        db: Session = Depends(get_db)
):
    """
    Garante que o usuário autenticado possua o campo 'email'.
    Evita falhas nos logs quando o token JWT não contém email.
    """
    usuario_email = current_user.get("email")
    if not usuario_email:
        usuario = db.query(m.Usuario).filter(m.Usuario.id == int(current_user.get("id"))).first()
        if usuario:
            usuario_email = usuario.email
            current_user["email"] = usuario.email
    return current_user


# ============================================================
# ENDPOINT: Criar teleconsulta
# ============================================================
@roteador.post(
    "/",
    response_model=TeleconsultaResponse,
    status_code=status.HTTP_201_CREATED
)
def criar_teleconsulta(
        consulta_id: int = Form(..., description="ID da consulta associada"),
        link_video: str = Form(..., description="Link para a videochamada"),
        db: Session = Depends(get_db),
        usuario_atual=Depends(obter_usuario_atual)
):
    """
    Cria uma nova teleconsulta associada a uma consulta existente.

    - **Acesso:** apenas MEDICO ou ADMIN
    - **Registra log** da operação
    """
    if usuario_atual.get("papel") not in ["MEDICO", "ADMIN"]:
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

    registrar_log(
        db=db,
        usuario_email=usuario_atual.get("email"),
        tabela="Teleconsulta",
        registro_id=nova_teleconsulta.id,
        acao="CREATE",
        detalhes=f"Teleconsulta criada para consulta {consulta_id} por {usuario_atual.get('email')}"
    )

    return nova_teleconsulta


# ============================================================
# ENDPOINT: Listar teleconsultas
# ============================================================
@roteador.get(
    "/",
    response_model=List[TeleconsultaResponse]
)
def listar_teleconsultas(
        db: Session = Depends(get_db),
        usuario_atual=Depends(obter_usuario_atual)
):
    """
    Lista todas as teleconsultas cadastradas.

    - **Acesso:** apenas MEDICO ou ADMIN
    - **Registra log** da operação
    """
    if usuario_atual.get("papel") not in ["MEDICO", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Sem permissão")

    teleconsultas = db.query(m.Teleconsulta).all()

    registrar_log(
        db=db,
        usuario_email=usuario_atual.get("email"),
        tabela="Teleconsulta",
        registro_id=None,
        acao="READ",
        detalhes=f"{usuario_atual.get('email')} listou todas as teleconsultas"
    )

    return teleconsultas


# ============================================================
# ENDPOINT: Cancelar teleconsulta
# ============================================================
@roteador.patch(
    "/{teleconsulta_id}/cancelar",
    response_model=TeleconsultaResponse
)
def cancelar_teleconsulta(
        teleconsulta_id: int,
        db: Session = Depends(get_db),
        usuario_atual=Depends(obter_usuario_atual)
):
    """
    Cancela uma teleconsulta existente pelo ID.

    - **Acesso:** apenas MEDICO ou ADMIN
    - **Registra log** da operação
    """
    if usuario_atual.get("papel") not in ["MEDICO", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Sem permissão")

    teleconsulta = db.query(m.Teleconsulta).filter(m.Teleconsulta.id == teleconsulta_id).first()
    if not teleconsulta:
        raise HTTPException(status_code=404, detail="Teleconsulta não encontrada")

    # Atualiza status para CANCELADA
    teleconsulta.status = m.StatusConsulta.CANCELADA
    db.commit()
    db.refresh(teleconsulta)

    registrar_log(
        db=db,
        usuario_email=usuario_atual.get("email"),
        tabela="Teleconsulta",
        registro_id=teleconsulta.id,
        acao="DELETE",
        detalhes=f"Teleconsulta {teleconsulta_id} cancelada por {usuario_atual.get('email')}"
    )

    return teleconsulta
