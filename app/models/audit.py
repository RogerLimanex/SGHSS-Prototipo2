# Modelo ORM para logs de auditoria do sistema

from sqlalchemy import Column, Integer, String, DateTime  # Tipos de coluna do SQLAlchemy
from sqlalchemy.sql import func  # Para funções SQL, como `now()`
from app.db import Base  # Base declarativa para os modelos


# =============================================================
# Classe AuditLog
# =============================================================
class AuditLog(Base):
    """
    Modelo de auditoria de ações no sistema.
    Cada registro representa uma operação realizada por um usuário
    (login, criação, atualização, deleção, etc.)
    """
    __tablename__ = "audit_logs"  # Nome da tabela no banco

    id = Column(Integer, primary_key=True, index=True)  # PK auto-increment
    usuario_email = Column(String, nullable=True)  # Email do usuário que executou a ação (opcional)
    tabela = Column(String, nullable=True)  # Nome da tabela afetada
    registro_id = Column(Integer, nullable=True)  # ID do registro afetado (opcional)
    acao = Column(String, nullable=False)  # Tipo de ação: CREATE, UPDATE, DELETE, LOGIN, etc.
    detalhes = Column(String, nullable=True)  # Informações adicionais sobre a ação
    data_hora = Column(DateTime(timezone=True), server_default=func.now())  # Timestamp do evento
