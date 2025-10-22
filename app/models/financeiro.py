# D:\ProjectSGHSS\app\models\financeiro.py
from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from app.db.session import Base


class Financeiro(Base):
    """
    Modelo Financeiro:
    - tipo: ENTRADA ou SAIDA
    - descricao: texto descritivo
    - valor: valor da movimentação
    - data: timestamp da operação
    """
    __tablename__ = "financeiro"

    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String, nullable=False)
    descricao = Column(String, nullable=False)
    valor = Column(Float, nullable=False)
    data = Column(DateTime, default=datetime.now)

    # Compatibilidade com o schema Pydantic
    @property
    def data_registro(self):
        return self.data
