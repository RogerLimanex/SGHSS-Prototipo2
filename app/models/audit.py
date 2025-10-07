# app/models/audit.py
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.db import Base


class AuditLog(Base):
    """
    Modelo de auditoria de ações no sistema.
    Cada registro representa uma operação realizada por um usuário (login, criação, atualização, etc.)
    """
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    usuario_email = Column(String, nullable=True)  # Email do usuário que realizou a ação (opcional)
    tabela = Column(String, nullable=True)  # Nome da tabela afetada
    registro_id = Column(Integer, nullable=True)  # ID do registro afetado (opcional)
    acao = Column(String, nullable=False)  # Ação realizada: CREATE, UPDATE, DELETE, LOGIN, etc.
    detalhes = Column(String, nullable=True)  # Descrição adicional da ação
    data_hora = Column(DateTime(timezone=True), server_default=func.now())  # Data/hora do evento
