from fastapi import APIRouter, Depends, HTTPException, status  # FastAPI imports
from sqlalchemy.orm import Session  # Sessão do SQLAlchemy
from typing import List, Optional  # Tipagens opcionais
from datetime import datetime  # Manipulação de datas
from app.db import get_db  # Sessão do banco
from app import models as m  # Models do projeto
from app.core import security  # Autenticação e segurança
from app.schemas.suprimento import SuprimentoResponse  # Schema de resposta
from app.utils.logs import registrar_log  # Função utilitária para logs

roteador = APIRouter()  # Inicializa o roteador de endpoints desta rota


# ============================================================
# Função auxiliar: obter usuário atual garantindo campo "email"
# ============================================================
def obter_usuario_atual(
        current_user=Depends(security.get_current_user),
        db: Session = Depends(get_db)
):
    """
    Retorna o usuário autenticado garantindo que o campo 'email' esteja presente.
    """
    usuario_email = current_user.get("email")
    if not usuario_email:  # Se o token não tiver email
        usuario = db.query(m.Usuario).filter(m.Usuario.id == int(current_user.get("id"))).first()
        if usuario:
            usuario_email = usuario.email
            current_user["email"] = usuario.email  # Atualiza dicionário
    return current_user  # Retorna usuário com email garantido


# ============================================================
# Função utilitária: formatar data no retorno
# ============================================================
def formatar_data_retorno(suprimento: m.Suprimento) -> dict:
    """
    Converte objeto ORM de Suprimento em dicionário
    e formata a data de validade para dd/mm/yyyy.
    """
    return {
        "id": suprimento.id,
        "nome": suprimento.nome,
        "quantidade": suprimento.quantidade,
        "data_validade": suprimento.data_validade.strftime("%d/%m/%Y") if suprimento.data_validade else None,
        "descricao": suprimento.descricao
    }


# ============================================================
# CRIAR SUPRIMENTO
# ============================================================
@roteador.post("/suprimentos", response_model=SuprimentoResponse, status_code=status.HTTP_201_CREATED)
def criar_suprimento(
        nome: str,
        quantidade: int,
        data_validade: Optional[str] = None,
        descricao: Optional[str] = None,
        db: Session = Depends(get_db),
        usuario_atual=Depends(obter_usuario_atual)
):
    """
    Cria um novo suprimento no sistema.

    - **Acesso restrito:** Apenas ADMIN
    - **Campos obrigatórios:** nome, quantidade
    - **Campos opcionais:** data_validade (dd/mm/yyyy), descricao
    """
    if usuario_atual["papel"] != "ADMIN":  # Valida permissão
        raise HTTPException(status_code=403, detail="Acesso negado: apenas ADMIN")

    # Converte data_validade de string para date
    validade = None
    if data_validade and data_validade.strip():
        try:
            validade = datetime.strptime(data_validade, "%d/%m/%Y").date()
        except ValueError:
            raise HTTPException(status_code=422, detail="Data inválida, use o formato dd/mm/yyyy")

    # Criação do registro ORM
    novo_suprimento = m.Suprimento(
        nome=nome,
        quantidade=quantidade,
        data_validade=validade,
        descricao=descricao
    )
    db.add(novo_suprimento)
    db.commit()
    db.refresh(novo_suprimento)  # Atualiza objeto com ID gerado

    # Log de auditoria
    registrar_log(
        db,
        usuario_atual["email"],
        "Suprimento",
        registro_id=novo_suprimento.id,
        acao="CREATE",
        detalhes=f"Criado suprimento '{nome}' com quantidade {quantidade}"
    )

    return formatar_data_retorno(novo_suprimento)  # Retorna dict formatado


# ============================================================
# LISTAR SUPRIMENTOS
# ============================================================
@roteador.get("/suprimentos", response_model=List[SuprimentoResponse])
def listar_suprimentos(
        db: Session = Depends(get_db),
        usuario_atual=Depends(obter_usuario_atual)
):
    """
    Lista todos os suprimentos cadastrados.

    - **Acesso restrito:** ADMIN ou MEDICO
    - **Retorno:** Lista de suprimentos com datas no formato dd/mm/yyyy
    """
    if usuario_atual["papel"] not in ["ADMIN", "MEDICO"]:  # Valida permissão
        raise HTTPException(status_code=403, detail="Acesso negado")

    suprimentos = db.query(m.Suprimento).all()  # Busca todos

    registrar_log(
        db,
        usuario_atual["email"],
        "Suprimento",
        acao="READ",
        detalhes="Listagem de suprimentos"
    )

    return [formatar_data_retorno(s) for s in suprimentos]  # Retorna lista formatada


# ============================================================
# ATUALIZAR SUPRIMENTO (PATCH)
# ============================================================
@roteador.patch("/suprimentos/{id}", response_model=SuprimentoResponse)
def atualizar_suprimento(
        id: int,
        nome: Optional[str] = None,
        quantidade: Optional[int] = None,
        data_validade: Optional[str] = None,
        descricao: Optional[str] = None,
        db: Session = Depends(get_db),
        usuario_atual=Depends(obter_usuario_atual)
):
    """
    Atualiza os campos de um suprimento existente pelo ID.

    - **Acesso restrito:** Apenas ADMIN
    - **Campos opcionais:** nome, quantidade, data_validade, descricao
    - **Formatação de data:** dd/mm/yyyy
    """
    if usuario_atual["papel"] != "ADMIN":  # Valida permissão
        raise HTTPException(status_code=403, detail="Acesso negado")

    suprimento = db.query(m.Suprimento).filter(m.Suprimento.id == id).first()
    if not suprimento:  # Se não existir
        raise HTTPException(status_code=404, detail="Suprimento não encontrado")

    if nome is not None and nome.strip():
        suprimento.nome = nome

    if quantidade is not None:
        suprimento.quantidade = quantidade

    if data_validade is not None and data_validade.strip():
        try:
            suprimento.data_validade = datetime.strptime(data_validade, "%d/%m/%Y").date()
        except ValueError:
            raise HTTPException(status_code=422, detail="Data inválida, use o formato dd/mm/yyyy")

    if descricao is not None:
        suprimento.descricao = descricao

    db.commit()
    db.refresh(suprimento)

    registrar_log(
        db,
        usuario_atual["email"],
        "Suprimento",
        registro_id=id,
        acao="UPDATE",
        detalhes=f"Atualizado suprimento {id}"
    )

    return formatar_data_retorno(suprimento)


# ============================================================
# ENDPOINT: EXCLUIR SUPRIMENTO
# ============================================================
@roteador.delete("/suprimentos/{id}", status_code=status.HTTP_200_OK)
def excluir_suprimento(
        id: int,
        db: Session = Depends(get_db),
        usuario_atual=Depends(obter_usuario_atual)
):
    """
    Exclui um suprimento pelo ID.

    - **Acesso restrito:** Apenas ADMIN
    - **Retorno:** Mensagem de confirmação
    """
    if usuario_atual["papel"] != "ADMIN":  # Valida permissão
        raise HTTPException(status_code=403, detail="Acesso negado: apenas ADMIN pode excluir suprimentos")

    suprimento = db.query(m.Suprimento).filter(m.Suprimento.id == id).first()
    if not suprimento:
        raise HTTPException(status_code=404, detail="Suprimento não encontrado")

    db.delete(suprimento)
    db.commit()

    registrar_log(
        db,
        usuario_atual["email"],
        "Suprimento",
        registro_id=id,
        acao="DELETE",
        detalhes=f"Suprimento excluído ID {id} por {usuario_atual.get('email')}"
    )

    return {"detail": "Suprimento excluído com sucesso"}  # Retorna mensagem de sucesso
