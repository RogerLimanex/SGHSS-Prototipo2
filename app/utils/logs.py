# D:\ProjectSGHSS\app\utils\logs.py
from sqlalchemy.orm import Session
from app import models as m
from datetime import datetime


def registrar_log(
        db: Session,
        usuario_email: str = None,
        tabela: str = None,
        registro_id: int = None,
        acao: str = None,
        descricao: str = None,
        detalhes: str = None
):
    """
    Registra uma ação no log de auditoria.

    Parâmetros:
    - usuario_email: email do usuário que executou a ação
    - tabela: nome da tabela afetada
    - registro_id: ID do registro afetado
    - acao: ação principal (ex: LOGIN, UPDATE, DELETE)
    - descricao: alternativa textual para acao
    - detalhes: informações adicionais sobre a ação
    """
    texto_acao = acao or descricao or "Ação não especificada"

    try:
        log = m.AuditLog(
            usuario_email=usuario_email,
            tabela=tabela,
            registro_id=registro_id,
            acao=texto_acao,
            detalhes=detalhes,
            data_hora=datetime.now()
        )
        db.add(log)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"❌ Erro ao registrar log: {e}")
