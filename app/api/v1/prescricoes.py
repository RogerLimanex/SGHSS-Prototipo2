from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.db import get_db
from app import models as m
from app.core import security
from app.schemas import PrescricaoResponse
from app.utils.logs import registrar_log  # Função utilitária para logs

roteador = APIRouter()


# ============================================================
# FUNÇÃO AUXILIAR: Obter usuário atual
# ============================================================
def obter_usuario_atual(
        current_user=Depends(security.get_current_user),
        db: Session = Depends(get_db)
):
    """
    Garante que o usuário autenticado tenha o campo 'email' disponível.
    Evita falhas nos logs quando o token JWT não contém o email.
    """
    usuario_email = current_user.get("email")
    if not usuario_email:
        usuario = db.query(m.Usuario).filter(m.Usuario.id == int(current_user.get("id"))).first()
        if usuario:
            usuario_email = usuario.email
            current_user["email"] = usuario.email
    return current_user


# ============================================================
# ENDPOINT: Criar prescrição
# ============================================================
@roteador.post("/prescricoes", response_model=PrescricaoResponse, status_code=status.HTTP_201_CREATED)
def criar_prescricao(
        paciente_id: int = Form(..., description="ID do paciente"),
        medico_id: int = Form(..., description="ID do médico"),
        medicamento: str = Form(..., description="Nome do medicamento"),
        dosagem: str = Form(..., description="Dosagem prescrita"),
        instrucoes: str = Form(..., description="Instruções para o paciente"),
        db: Session = Depends(get_db),
        usuario_atual=Depends(obter_usuario_atual)
):
    """
    Cria uma nova prescrição médica para um paciente.

    - **Acesso:** apenas MEDICO ou ADMIN
    - **Registra log** da criação
    """
    if usuario_atual.get("papel") not in ["MEDICO", "ADMIN"]:
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

    registrar_log(
        db=db,
        usuario_email=usuario_atual.get("email"),
        tabela="Receita",
        registro_id=nova_prescricao.id,
        acao="CREATE",
        detalhes=f"Prescrição criada para paciente {paciente_id} pelo médico {medico_id}"
    )

    return nova_prescricao


# ============================================================
# ENDPOINT: Listar prescrições
# ============================================================
@roteador.get("/prescricoes", response_model=List[PrescricaoResponse])
def listar_prescricoes(
        db: Session = Depends(get_db),
        usuario_atual=Depends(obter_usuario_atual)
):
    """
    Lista todas as prescrições médicas cadastradas.

    - **Acesso:** apenas MEDICO ou ADMIN
    - **Registra log** da operação
    """
    if usuario_atual.get("papel") not in ["MEDICO", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Sem permissão")

    prescricoes = db.query(m.Receita).all()

    registrar_log(
        db=db,
        usuario_email=usuario_atual.get("email"),
        tabela="Receita",
        acao="READ",
        detalhes=f"{usuario_atual.get('email')} listou todas as prescrições"
    )

    return prescricoes


# ============================================================
# ENDPOINT: Cancelar prescrição
# ============================================================
@roteador.patch("/prescricoes/{prescricao_id}/cancelar", response_model=PrescricaoResponse)
def cancelar_prescricao(
        prescricao_id: int,
        db: Session = Depends(get_db),
        usuario_atual=Depends(obter_usuario_atual)
):
    """
    Cancela uma prescrição médica existente.

    - **Acesso:** apenas MEDICO ou ADMIN
    - **Altera status da prescrição para 'CANCELADA'
    - **Registra log** do cancelamento
    """
    if usuario_atual.get("papel") not in ["MEDICO", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Sem permissão")

    prescricao = db.query(m.Receita).filter(m.Receita.id == prescricao_id).first()
    if not prescricao:
        raise HTTPException(status_code=404, detail="Prescrição não encontrada")

    prescricao.status = "CANCELADA"
    db.commit()
    db.refresh(prescricao)

    registrar_log(
        db=db,
        usuario_email=usuario_atual.get("email"),
        tabela="Receita",
        registro_id=prescricao.id,
        acao="DELETE",
        detalhes=f"Prescrição {prescricao_id} cancelada pelo usuário {usuario_atual.get('email')}"
    )

    return prescricao
