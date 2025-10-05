# app/models/audit.py
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.db import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    usuario_email = Column(String, nullable=False)  # usuário que realizou a ação
    tabela = Column(String, nullable=False)  # tabela afetada
    registro_id = Column(Integer, nullable=False)  # ID do registro afetado
    acao = Column(String, nullable=False)  # CREATE, UPDATE, CANCEL, DELETE
    detalhes = Column(String, nullable=True)  # JSON ou descrição das alterações
    data_hora = Column(DateTime(timezone=True), server_default=func.now())
