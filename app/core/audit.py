# app/core/audit.py
from sqlalchemy.orm import Session
from app.models.audit import AuditLog
import json


def registrar_log(db: Session, usuario_email: str, tabela: str, registro_id: int, acao: str, detalhes: dict = None):
    log = AuditLog(
        usuario_email=usuario_email,
        tabela=tabela,
        registro_id=registro_id,
        acao=acao,
        detalhes=json.dumps(detalhes) if detalhes else None
    )
    db.add(log)
    db.commit()
