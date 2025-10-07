# D:\ProjectSGHSS\app\api\v1\auditoria.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db_session
from app.models.audit import AuditLog
from app.core import security

roteador = APIRouter()


@roteador.get("/audit_logs", summary="Listar logs de auditoria", tags=["Auditoria"])
def listar_logs(
        current_user=Depends(security.get_current_user),
        db: Session = Depends(get_db_session)
):
    """
    Lista todos os registros de auditoria do sistema (somente ADMIN).
    """
    # Verifica se o usuário logado é ADMIN
    if current_user.get("role") != "ADMIN":
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
