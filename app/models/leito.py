# Modelo ORM para leitos hospitalares

from sqlalchemy import Column, Integer, String, ForeignKey  # Tipos de coluna e FK
from sqlalchemy.orm import relationship  # Para relacionamento ORM
from app.db import Base  # Base declarativa para modelos


# =============================================================
# Classe Leito
# =============================================================
class Leito(Base):
    """
    Modelo de banco de dados que representa um leito hospitalar.
    Contém informações de número, status e paciente associado.
    """
    __tablename__ = "leitos"  # Nome da tabela no banco

    id = Column(Integer, primary_key=True, index=True)  # PK auto-increment
    numero = Column(String(50), nullable=False)  # Número ou identificador do leito
    status = Column(String(50), nullable=False)  # Status do leito (ex.: LIVRE, OCUPADO)
    paciente_id = Column(Integer, ForeignKey("pacientes.id"), nullable=True)  # FK opcional para paciente

    # Relacionamento ORM opcional com o paciente
    paciente = relationship("Paciente", back_populates="leitos")
