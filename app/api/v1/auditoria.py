# D:\ProjectSGHSS\app\api\v1\auditoria.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.models.audit import AuditLog
from app.core import security

roteador = APIRouter()


# --------------------------
# Obter usuário atual com email garantido
# --------------------------
def obter_usuario_atual(
        current_user=Depends(security.get_current_user),
        db: Session = Depends(get_db)
):
    """
    Retorna o usuário autenticado com email garantido.
    Evita falhas nos logs quando o token JWT não contém o campo 'email'.
    """
    usuario_email = current_user.get("email")
    if not usuario_email:
        from app import models as m
        usuario = db.query(m.Usuario).filter(m.Usuario.id == int(current_user.get("id"))).first()
        if usuario:
            usuario_email = usuario.email
            current_user["email"] = usuario.email
    return current_user


# --------------------------
# Listar logs de auditoria
# --------------------------
@roteador.get("/audit_logs", summary="Listar logs de auditoria", tags=["Auditoria"])
def listar_logs(
        usuario_atual=Depends(obter_usuario_atual),
        db: Session = Depends(get_db)
):
    """
    Lista todos os registros de auditoria do sistema (somente ADMIN).
    """
    # Verifica se o usuário logado é ADMIN
    if usuario_atual.get("papel") != "ADMIN":
        raise HTTPException(status_code=403, detail="Acesso negado: apenas ADMIN")

    logs = db.query(AuditLog).order_by(AuditLog.data_hora.desc()).all()

    return [
        {
            "id": log.id,
            "usuario_email": log.usuario_email,
            "tabela": log.tabela,
            "registro_id": log.registro_id,
            "acao": log.acao,
            "detalhes": log.detalhes,
            "data_hora": log.data_hora,
        }
        for log in logs
    ]
