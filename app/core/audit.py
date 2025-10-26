from sqlalchemy.orm import Session  # Sessão do SQLAlchemy
from app.models.audit import AuditLog  # Model do log de auditoria
import json  # Para serializar dicionários em JSON


def registrar_log(db: Session, usuario_email: str, tabela: str, registro_id: int, acao: str, detalhes: dict = None):
    # Cria um novo objeto de log
    log = AuditLog(
        usuario_email=usuario_email,
        tabela=tabela,
        registro_id=registro_id,
        acao=acao,
        detalhes=json.dumps(detalhes) if detalhes else None  # Converte dict em JSON, se houver
    )
    db.add(log)  # Adiciona à sessão
    db.commit()  # Persiste no banco
