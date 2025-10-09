# D:\ProjectSGHSS\app\api\v1\prontuario.py
from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.db import get_db_session
from app import models as m
from app.core import security
from app.schemas import ProntuarioMedicoResponse
from app.utils.logs import registrar_log  # import do util de logs

roteador = APIRouter()


# ----------------------------
# Obter usuário atual com email garantido
# ----------------------------
def obter_usuario_atual(
        current_user=Depends(security.get_current_user),
        db: Session = Depends(get_db_session)
):
    """Garante que o usuário atual tenha o campo 'email' disponível."""
    usuario_email = current_user.get("email")
    if not usuario_email:
        usuario = db.query(m.Usuario).filter(m.Usuario.id == int(current_user.get("id"))).first()
        if usuario:
            usuario_email = usuario.email
            current_user["email"] = usuario.email
    return current_user


# ----------------------------
# Criar prontuário médico
# ----------------------------
@roteador.post("/prontuarios", response_model=ProntuarioMedicoResponse, status_code=status.HTTP_201_CREATED)
def criar_prontuario(
        paciente_id: int = Form(...),
        medico_id: int = Form(...),
        descricao: str = Form(...),
        db: Session = Depends(get_db_session),
        usuario_atual=Depends(obter_usuario_atual)
):
    if usuario_atual.get("papel") not in ["MEDICO", "ADMIN"]:
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

    registrar_log(
        db=db,
        usuario_email=usuario_atual.get("email"),
        tabela="Prontuario",
        registro_id=novo_prontuario.id,
        acao="CREATE",
        detalhes=f"Prontuário criado para paciente {paciente_id} pelo médico {medico_id}"
    )

    return novo_prontuario


# ----------------------------
# Listar prontuários médicos
# ----------------------------
@roteador.get("/prontuarios", response_model=List[ProntuarioMedicoResponse])
def listar_prontuarios(
        db: Session = Depends(get_db_session),
        usuario_atual=Depends(obter_usuario_atual)
):
    if usuario_atual.get("papel") not in ["MEDICO", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Sem permissão")

    prontuarios = db.query(m.Prontuario).all()

    registrar_log(
        db=db,
        usuario_email=usuario_atual.get("email"),
        tabela="Prontuario",
        acao="READ",
        detalhes=f"{usuario_atual.get('email')} listou todos os prontuários"
    )

    return prontuarios


# ----------------------------
# Cancelar prontuário médico
# ----------------------------
@roteador.post("/prontuarios/{prontuario_id}/cancelar", response_model=ProntuarioMedicoResponse)
def cancelar_prontuario(
        prontuario_id: int,
        db: Session = Depends(get_db_session),
        usuario_atual=Depends(obter_usuario_atual)
):
    if usuario_atual.get("papel") not in ["MEDICO", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Sem permissão")

    prontuario = db.query(m.Prontuario).filter(m.Prontuario.id == prontuario_id).first()
    if not prontuario:
        raise HTTPException(status_code=404, detail="Prontuário não encontrado")

    prontuario.status = "CANCELADO"  # Marca como cancelado, sem excluir do banco
    db.commit()
    db.refresh(prontuario)

    registrar_log(
        db=db,
        usuario_email=usuario_atual.get("email"),
        tabela="Prontuario",
        registro_id=prontuario.id,
        acao="DELETE",
        detalhes=f"Prontuário {prontuario_id} cancelado pelo usuário {usuario_atual.get('email')}"
    )

    return prontuario
