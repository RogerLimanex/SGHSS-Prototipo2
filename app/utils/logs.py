from sqlalchemy.orm import Session
from app import models as m
from datetime import datetime


def registrar_log(db: Session, usuario_email: str, tabela: str, registro_id: int, acao: str, detalhes: str = None):
    """
    Registra uma ação no log de auditoria
    """
    log = m.AuditLog(
        usuario_email=usuario_email,
        tabela=tabela,
        registro_id=registro_id,
        acao=acao,
        detalhes=detalhes,
        data_hora=datetime.now()
    )
    db.add(log)
    db.commit()
