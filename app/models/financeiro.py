# Modelo ORM para registros financeiros

from sqlalchemy import Column, Integer, String, Float, DateTime  # Tipos de coluna do SQLAlchemy
from datetime import datetime  # Para default de timestamp
from app.db.session import Base  # Base declarativa para modelos


# =============================================================
# Classe Financeiro
# =============================================================
class Financeiro(Base):
    """
    Modelo Financeiro:
    - tipo: ENTRADA ou SAIDA
    - descricao: descrição da movimentação financeira
    - valor: valor da entrada ou saída
    - data: timestamp da operação
    """
    __tablename__ = "financeiro"  # Nome da tabela no banco

    id = Column(Integer, primary_key=True, index=True)  # PK auto-increment
    tipo = Column(String, nullable=False)  # Tipo da movimentação: ENTRADA ou SAIDA
    descricao = Column(String, nullable=False)  # Descrição textual da movimentação
    valor = Column(Float, nullable=False)  # Valor monetário da movimentação
    data = Column(DateTime, default=datetime.now)  # Timestamp da operação

    # =========================================================
    # Propriedade compatível com Pydantic para retorno
    # =========================================================
    @property
    def data_registro(self):
        return self.data
