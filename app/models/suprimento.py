# D:\ProjectSGHSS\app\models\suprimento.py
from sqlalchemy import Column, Integer, String, Date
from app.db import Base


class Suprimento(Base):
    """
    Modelo de banco de dados que representa um suprimento hospitalar.
    Armazena informações como nome, quantidade em estoque,
    data de validade e uma descrição opcional.
    """
    __tablename__ = "suprimentos"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(150), nullable=False)
    quantidade = Column(Integer, nullable=False)
    data_validade = Column(Date, nullable=True)
    descricao = Column(String(255), nullable=True)
