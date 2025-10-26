from fastapi import APIRouter, Depends, HTTPException, status, Form  # FastAPI imports
from sqlalchemy.orm import Session  # Sessão do SQLAlchemy
from typing import List  # Tipagem para listas
from datetime import datetime  # Datas e horários

from app.db import get_db  # Sessão do banco
from app import models as m  # Models do projeto
from app.core import security  # Segurança e autenticação
from app.schemas import TeleconsultaResponse  # Schema de resposta
from app.utils.logs import registrar_log  # Função utilitária de logs

roteador = APIRouter()  # Inicializa roteador de endpoints


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
    if not usuario_email:  # Se não houver email no token
        usuario = db.query(m.Usuario).filter(m.Usuario.id == int(current_user.get("id"))).first()
        if usuario:
            usuario_email = usuario.email
            current_user["email"] = usuario.email  # Atualiza dicionário do usuário
    return current_user  # Retorna usuário com email garantido


# ============================================================
# 1️⃣ ENDPOINT: Criar teleconsulta
# ============================================================
@roteador.post(
    "/",
    response_model=TeleconsultaResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Teleconsultas"]
)
def criar_teleconsulta(
        consulta_id: int = Form(..., description="ID da consulta associada"),  # ID da consulta vinculada
        link_video: str = Form(..., description="Link para a videochamada"),  # Link da teleconsulta
        db: Session = Depends(get_db),
        usuario_atual=Depends(obter_usuario_atual)
):
    """
    Cria uma nova teleconsulta associada a uma consulta existente.

    - **Acesso:** apenas MEDICO ou ADMIN
    - **Registra log** da operação
    """
    if usuario_atual.get("papel") not in ["MEDICO", "ADMIN"]:  # Valida permissão
        raise HTTPException(status_code=403, detail="Sem permissão")

    # Cria objeto ORM
    nova_teleconsulta = m.Teleconsulta(
        consulta_id=consulta_id,
        link_video=link_video,
        data_hora=datetime.now(),  # Hora atual
        status=m.StatusConsulta.AGENDADA  # Status inicial
    )
    db.add(nova_teleconsulta)
    db.commit()
    db.refresh(nova_teleconsulta)  # Atualiza objeto com ID gerado

    # Log de auditoria
    registrar_log(
        db=db,
        usuario_email=usuario_atual.get("email"),
        tabela="Teleconsulta",
        registro_id=nova_teleconsulta.id,
        acao="CREATE",
        detalhes=f"Teleconsulta criada para consulta {consulta_id} por {usuario_atual.get('email')}"
    )

    return nova_teleconsulta  # Retorna objeto criado


# ============================================================
# 2️⃣ ENDPOINT: Listar teleconsultas
# ============================================================
@roteador.get(
    "/",
    response_model=List[TeleconsultaResponse],
    tags=["Teleconsultas"]
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
    if usuario_atual.get("papel") not in ["MEDICO", "ADMIN"]:  # Valida permissão
        raise HTTPException(status_code=403, detail="Sem permissão")

    teleconsultas = db.query(m.Teleconsulta).all()  # Busca todas teleconsultas

    # Log de auditoria
    registrar_log(
        db=db,
        usuario_email=usuario_atual.get("email"),
        tabela="Teleconsulta",
        registro_id=None,
        acao="READ",
        detalhes=f"{usuario_atual.get('email')} listou todas as teleconsultas"
    )

    return teleconsultas  # Retorna lista completa


# ============================================================
# 3️⃣ ENDPOINT: Cancelar teleconsulta
# ============================================================
@roteador.patch(
    "/{teleconsulta_id}/cancelar",
    response_model=TeleconsultaResponse,
    tags=["Teleconsultas"]
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
    if usuario_atual.get("papel") not in ["MEDICO", "ADMIN"]:  # Valida permissão
        raise HTTPException(status_code=403, detail="Sem permissão")

    teleconsulta = db.query(m.Teleconsulta).filter(m.Teleconsulta.id == teleconsulta_id).first()
    if not teleconsulta:  # Se não existir
        raise HTTPException(status_code=404, detail="Teleconsulta não encontrada")

    teleconsulta.status = m.StatusConsulta.CANCELADA  # Atualiza status
    db.commit()
    db.refresh(teleconsulta)

    # Log de auditoria
    registrar_log(
        db=db,
        usuario_email=usuario_atual.get("email"),
        tabela="Teleconsulta",
        registro_id=teleconsulta.id,
        acao="DELETE",
        detalhes=f"Teleconsulta {teleconsulta_id} cancelada por {usuario_atual.get('email')}"
    )

    return teleconsulta  # Retorna teleconsulta atualizada
