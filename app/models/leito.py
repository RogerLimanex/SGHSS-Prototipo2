# D:\ProjectSGHSS\app\models\leito.py
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db import Base


class Leito(Base):
    """
    Modelo de banco de dados que representa um leito hospitalar.
    Guarda informações como número do leito, status e paciente associado.
    """
    __tablename__ = "leitos"

    id = Column(Integer, primary_key=True, index=True)
    numero = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False)
    paciente_id = Column(Integer, ForeignKey("pacientes.id"), nullable=True)

    # Relacionamento opcional com paciente, se existir tabela Paciente
    paciente = relationship("Paciente", back_populates="leitos")
