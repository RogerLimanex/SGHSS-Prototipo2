# D:\ProjectSGHSS\app\utils\logs.py
from sqlalchemy.orm import Session  # Sessão do SQLAlchemy para interagir com o banco
from app import models as m  # Importa todos os modelos do projeto
from datetime import datetime  # Para registrar data/hora do log


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
    Registra uma ação no log de auditoria do sistema.

    Parâmetros:
    - usuario_email: email do usuário que executou a ação
    - tabela: nome da tabela afetada
    - registro_id: ID do registro afetado
    - acao: ação principal (ex: LOGIN, CREATE, UPDATE, DELETE)
    - descricao: alternativa textual para acao
    - detalhes: informações adicionais sobre a ação
    """
    texto_acao = acao or descricao or "Ação não especificada"  # Prioriza ação, depois descrição, depois texto padrão

    try:
        log = m.AuditLog(
            usuario_email=usuario_email,  # Email do usuário que executou a ação
            tabela=tabela,  # Tabela afetada
            registro_id=registro_id,  # ID do registro afetado
            acao=texto_acao,  # Ação principal ou descrição
            detalhes=detalhes,  # Detalhes adicionais da ação
            data_hora=datetime.now()  # Timestamp atual
        )
        db.add(log)  # Adiciona à sessão
        db.commit()  # Confirma a inserção no banco
    except Exception as e:
        db.rollback()  # Reverte caso haja erro
        print(f"❌ Erro ao registrar log: {e}")  # Log de erro no console
