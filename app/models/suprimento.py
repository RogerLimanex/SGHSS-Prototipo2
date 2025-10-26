# D:\ProjectSGHSS\app\models\suprimento.py
# Modelo de suprimentos hospitalares

from sqlalchemy import Column, Integer, String, Date  # Tipos de colunas SQLAlchemy
from app.db import Base  # Base declarativa do projeto


class Suprimento(Base):
    """
    Representa um suprimento hospitalar.
    Armazena nome, quantidade em estoque, data de validade e descrição opcional.
    """
    __tablename__ = "suprimentos"

    id = Column(Integer, primary_key=True, index=True)  # ID único do suprimento
    nome = Column(String(150), nullable=False)  # Nome do item
    quantidade = Column(Integer, nullable=False)  # Quantidade disponível
    data_validade = Column(Date, nullable=True)  # Data de validade (opcional)
    descricao = Column(String(255), nullable=True)  # Descrição adicional (opcional)
