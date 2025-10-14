from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.db import get_db
from app import models as m
from app.core import security
from app.schemas import ProntuarioResponse
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
# ENDPOINT: Criar registro de prontuário
# ============================================================
@roteador.post(
    "/",
    response_model=ProntuarioResponse,
    status_code=status.HTTP_201_CREATED
)
def criar_prontuario(
        consulta_id: int = Form(..., description="ID da consulta relacionada"),
        anotacoes: str = Form(..., description="Anotações médicas e observações do prontuário"),
        db: Session = Depends(get_db),
        usuario_atual=Depends(obter_usuario_atual)
):
    """
    Cria um novo registro de prontuário para uma consulta.

    - **Acesso:** apenas MÉDICO ou ADMIN
    - **Registra log** da operação
    """
    if usuario_atual.get("papel") not in ["MEDICO", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Sem permissão")

    novo_prontuario = m.Prontuario(
        consulta_id=consulta_id,
        anotacoes=anotacoes,
        data_registro=datetime.now()
    )

    db.add(novo_prontuario)
    db.commit()
    db.refresh(novo_prontuario)

    registrar_log(
        db=db,
        usuario_email=usuario_atual.get("email"),
        tabela="Prontuario",
        registro_id=novo_prontuario.id,
        acao="CREATE",
        detalhes=f"Prontuário criado para consulta {consulta_id} por {usuario_atual.get('email')}"
    )

    return novo_prontuario


# ============================================================
# ENDPOINT: Listar prontuários
# ============================================================
@roteador.get(
    "/",
    response_model=List[ProntuarioResponse]
)
def listar_prontuarios(
        db: Session = Depends(get_db),
        usuario_atual=Depends(obter_usuario_atual)
):
    """
    Lista todos os prontuários cadastrados.

    - **Acesso:** apenas MÉDICO ou ADMIN
    - **Registra log** da operação
    """
    if usuario_atual.get("papel") not in ["MEDICO", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Sem permissão")

    prontuarios = db.query(m.Prontuario).all()

    registrar_log(
        db=db,
        usuario_email=usuario_atual.get("email"),
        tabela="Prontuario",
        registro_id=None,
        acao="READ",
        detalhes=f"{usuario_atual.get('email')} listou todos os prontuários"
    )

    return prontuarios


# ============================================================
# ENDPOINT: Excluir (ou cancelar) prontuário
# ============================================================
@roteador.delete(
    "/{prontuario_id}",
    response_model=ProntuarioResponse
)
def excluir_prontuario(
        prontuario_id: int,
        db: Session = Depends(get_db),
        usuario_atual=Depends(obter_usuario_atual)
):
    """
    Exclui um prontuário existente pelo ID.

    - **Acesso:** apenas ADMIN
    - **Registra log** da operação
    """
    if usuario_atual.get("papel") != "ADMIN":
        raise HTTPException(status_code=403, detail="Sem permissão")

    prontuario = db.query(m.Prontuario).filter(m.Prontuario.id == prontuario_id).first()
    if not prontuario:
        raise HTTPException(status_code=404, detail="Prontuário não encontrado")

    db.delete(prontuario)
    db.commit()

    registrar_log(
        db=db,
        usuario_email=usuario_atual.get("email"),
        tabela="Prontuario",
        registro_id=prontuario_id,
        acao="DELETE",
        detalhes=f"Prontuário {prontuario_id} excluído por {usuario_atual.get('email')}"
    )

    return prontuario
