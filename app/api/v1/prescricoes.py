from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.db import get_db_session
from app import models as m
from app.core import security
from app.schemas import PrescricaoResponse
from app.utils.logs import registrar_log  # import do util de logs

roteador = APIRouter()


# ----------------------------
# Dependência para obter o usuário atual
# ----------------------------
def obter_usuario_atual(current_user=Depends(security.get_current_user)):
    return current_user


# ----------------------------
# Criar prescrição médica com campos separados
# ----------------------------
@roteador.post("/prescricoes", response_model=PrescricaoResponse, status_code=status.HTTP_201_CREATED)
def criar_prescricao(
        paciente_id: int = Form(...),
        medico_id: int = Form(...),
        medicamento: str = Form(...),
        dosagem: str = Form(...),
        instrucoes: str = Form(...),
        db: Session = Depends(get_db_session),
        usuario_atual=Depends(obter_usuario_atual)
):
    """
    Cria uma nova prescrição médica para um paciente.
    Apenas ADMIN ou MEDICO podem criar.
    """
    if usuario_atual.get("role") not in ["MEDICO", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Sem permissão")

    nova_prescricao = m.Receita(
        paciente_id=paciente_id,
        medico_id=medico_id,
        medicamento=medicamento,
        dosagem=dosagem,
        instrucoes=instrucoes,
        data_hora=datetime.now()
    )
    db.add(nova_prescricao)
    db.commit()
    db.refresh(nova_prescricao)

    # ----------------------------
    # Registrar log da criação
    # ----------------------------
    registrar_log(
        db=db,
        usuario_email=usuario_atual.get("email"),  # corrigido
        tabela="Receita",
        registro_id=nova_prescricao.id,
        acao="CREATE",
        descricao=f"Prescrição criada para paciente {paciente_id} pelo médico {medico_id}"
    )

    return nova_prescricao


# ----------------------------
# Listar prescrições médicas
# ----------------------------
@roteador.get("/prescricoes", response_model=List[PrescricaoResponse])
def listar_prescricoes(
        db: Session = Depends(get_db_session),
        usuario_atual=Depends(obter_usuario_atual)
):
    """
    Lista todas as prescrições médicas cadastradas.
    Apenas ADMIN ou MEDICO podem visualizar.
    """
    if usuario_atual.get("role") not in ["MEDICO", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Sem permissão")

    return db.query(m.Receita).all()


# ----------------------------
# Cancelar prescrição médica
# ----------------------------
@roteador.patch("/prescricoes/{prescricao_id}/cancelar", response_model=PrescricaoResponse)
def cancelar_prescricao(
        prescricao_id: int,
        db: Session = Depends(get_db_session),
        usuario_atual=Depends(obter_usuario_atual)
):
    """
    Cancela (inativa) uma prescrição existente.
    Apenas ADMIN ou MEDICO podem cancelar.
    """
    if usuario_atual.get("role") not in ["MEDICO", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Sem permissão")

    prescricao = db.query(m.Receita).filter(m.Receita.id == prescricao_id).first()
    if not prescricao:
        raise HTTPException(status_code=404, detail="Prescrição não encontrada")

    prescricao.status = "CANCELADA"
    db.commit()
    db.refresh(prescricao)

    # ----------------------------
    # Registrar log do cancelamento
    # ----------------------------
    registrar_log(
        db=db,
        usuario_email=usuario_atual.get("email"),  # corrigido
        tabela="Receita",
        registro_id=prescricao.id,
        acao="DELETE",
        descricao=f"Prescrição {prescricao_id} cancelada pelo usuário"
    )

    return prescricao
