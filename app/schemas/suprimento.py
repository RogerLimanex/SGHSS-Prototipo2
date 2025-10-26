# D:\ProjectSGHSS\app\schemas\suprimento.py
from pydantic import BaseModel, validator  # BaseModel para schemas, validator para validação de campos
from datetime import date, datetime  # date para datas, datetime para parsing de string
from typing import Optional  # Campos opcionais


# ----------------------------
# Schema base para Suprimento
# ----------------------------
class SuprimentoBase(BaseModel):
    """
    Schema base para criação e atualização de suprimentos.
    Define os campos esperados ao criar ou editar um suprimento.
    """
    nome: str  # Nome do suprimento, obrigatório
    quantidade: int  # Quantidade em estoque, obrigatório
    data_validade: Optional[date] = None  # Data de validade, opcional
    descricao: Optional[str] = None  # Descrição adicional, opcional

    @validator("data_validade", pre=True)
    def converter_data_validade(cls, valor):
        """
        Converte a data informada como string no formato dd/mm/yyyy
        para um objeto datetime.date.
        Caso o campo venha vazio ou None, mantém como None.
        """
        if isinstance(valor, str):
            try:
                return datetime.strptime(valor, "%d/%m/%Y").date()
            except ValueError:
                raise ValueError("Formato de data inválido. Use dd/mm/yyyy.")
        return valor


# ----------------------------
# Schema de resposta de Suprimento
# ----------------------------
class SuprimentoResponse(SuprimentoBase):
    """
    Schema de resposta retornado pela API.
    Inclui o ID do suprimento e permite leitura ORM.
    """
    id: int  # ID único do suprimento no banco

    class Config:
        from_attributes = True  # Compatível com objetos ORM (Pydantic v2)
