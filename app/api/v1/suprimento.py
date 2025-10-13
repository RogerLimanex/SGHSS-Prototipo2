# D:\ProjectSGHSS\app\api\v1\suprimento.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import date
from app.db import get_db
from app import models as m
from app.core import security
from app.schemas.suprimento import SuprimentoBase, SuprimentoResponse
from app.utils.logs import registrar_log

roteador = APIRouter()


# ----------------------------
# Obter usuário atual garantindo email
# ----------------------------
def obter_usuario_atual(current_user=Depends(security.get_current_user), db: Session = Depends(get_db)):
    """
    Garante que o usuário autenticado possua o campo 'email'.
    Evita falhas nos logs quando o token JWT não contém email.
    """
    usuario_email = current_user.get("email")
    if not usuario_email:
        usuario = db.query(m.Usuario).filter(m.Usuario.id == int(current_user.get("id"))).first()
        if usuario:
            usuario_email = usuario.email
            current_user["email"] = usuario.email
    return current_user


# ----------------------------
# Criar novo suprimento
# ----------------------------
@roteador.post("/suprimentos", response_model=SuprimentoResponse)
def criar_suprimento(
        suprimento: SuprimentoBase,
        db: Session = Depends(get_db),
        usuario_atual=Depends(obter_usuario_atual)
):
    """
    Cria um novo registro de suprimento.
    Permissão restrita a usuários ADMIN.
    Registra log da operação.
    """
    if usuario_atual["papel"] != "ADMIN":
        raise HTTPException(status_code=403, detail="Acesso negado: apenas ADMIN")

    novo = m.Suprimento(**suprimento.dict())
    db.add(novo)
    db.commit()
    db.refresh(novo)

    registrar_log(
        db,
        usuario_atual["email"],
        "Suprimento",
        registro_id=novo.id,
        acao="CREATE",
        detalhes=f"Criado suprimento {novo.nome}"
    )
    return novo


# ----------------------------
# Listar todos os suprimentos
# ----------------------------
@roteador.get("/suprimentos", response_model=List[SuprimentoResponse])
def listar_suprimentos(db: Session = Depends(get_db), usuario_atual=Depends(obter_usuario_atual)):
    """
    Lista todos os suprimentos cadastrados.
    Permissão para usuários ADMIN e MEDICO.
    Registra log da operação.
    """
    if usuario_atual["papel"] not in ["ADMIN", "MEDICO"]:
        raise HTTPException(status_code=403, detail="Acesso negado")

    lista = db.query(m.Suprimento).all()

    registrar_log(
        db,
        usuario_atual["email"],
        "Suprimento",
        acao="READ",
        detalhes="Listagem de suprimentos"
    )
    return lista


# ----------------------------
# Atualizar suprimento existente
# ----------------------------
@roteador.put("/suprimentos/{id}", response_model=SuprimentoResponse)
def atualizar_suprimento(
        id: int,
        dados: SuprimentoBase,
        db: Session = Depends(get_db),
        usuario_atual=Depends(obter_usuario_atual)
):
    """
    Atualiza um suprimento existente pelo ID.
    Permissão restrita a usuários ADMIN.
    Registra log da operação.
    """
    if usuario_atual["papel"] != "ADMIN":
        raise HTTPException(status_code=403, detail="Acesso negado")

    sup = db.query(m.Suprimento).filter(m.Suprimento.id == id).first()
    if not sup:
        raise HTTPException(status_code=404, detail="Suprimento não encontrado")

    # Atualiza campos do suprimento com os dados recebidos
    for campo, valor in dados.dict().items():
        setattr(sup, campo, valor)

    db.commit()
    db.refresh(sup)

    registrar_log(
        db,
        usuario_atual["email"],
        "Suprimento",
        registro_id=id,
        acao="UPDATE",
        detalhes=f"Atualizado suprimento {id}"
    )
    return sup


# ----------------------------
# Remover suprimento
# ----------------------------
@roteador.delete("/suprimentos/{id}")
def remover_suprimento(
        id: int,
        db: Session = Depends(get_db),
        usuario_atual=Depends(obter_usuario_atual)
):
    """
    Remove um suprimento pelo ID.
    Permissão restrita a usuários ADMIN.
    Registra log da operação.
    """
    if usuario_atual["papel"] != "ADMIN":
        raise HTTPException(status_code=403, detail="Acesso negado")

    sup = db.query(m.Suprimento).filter(m.Suprimento.id == id).first()
    if not sup:
        raise HTTPException(status_code=404, detail="Suprimento não encontrado")

    db.delete(sup)
    db.commit()

    registrar_log(
        db,
        usuario_atual["email"],
        "Suprimento",
        registro_id=id,
        acao="DELETE",
        detalhes=f"Removido suprimento {id}"
    )

    return {"detail": "Removido com sucesso"}
