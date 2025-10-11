# D:\ProjectSGHSS\app\api\v1\leito.py
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from app.db import get_db
from app import models as m
from app.core import security
from app.schemas.leito import LeitoBase, LeitoResponse
from app.utils.logs import registrar_log

roteador = APIRouter()


# ----------------------------
# Obter usuário atual com email
# ----------------------------
def obter_usuario_atual(
        current_user=Depends(security.get_current_user),
        db: Session = Depends(get_db)
):
    usuario_email = current_user.get("email")
    if not usuario_email:
        usuario = db.query(m.Usuario).filter(m.Usuario.id == int(current_user.get("id"))).first()
        if usuario:
            usuario_email = usuario.email
            current_user["email"] = usuario.email
    return current_user


# ----------------------------
# Criar leito hospitalar
# ----------------------------
@roteador.post("/leitos", response_model=LeitoResponse, status_code=status.HTTP_201_CREATED)
def criar_leito(
        leito: LeitoBase,
        db: Session = Depends(get_db),
        usuario_atual=Depends(obter_usuario_atual)
):
    if usuario_atual.get("papel") != "ADMIN":
        raise HTTPException(status_code=403, detail="Acesso negado: apenas ADMIN")

    novo_leito = m.Leito(
        numero=leito.numero,
        status=leito.status,
        paciente_id=leito.paciente_id
    )
    db.add(novo_leito)
    db.commit()
    db.refresh(novo_leito)

    registrar_log(db, usuario_atual["email"], "Leito", novo_leito.id, "CREATE",
                  f"Leito {leito.numero} criado com status {leito.status}")

    return novo_leito


# ----------------------------
# Listar leitos
# ----------------------------
@roteador.get("/leitos", response_model=List[LeitoResponse])
def listar_leitos(
        db: Session = Depends(get_db),
        usuario_atual=Depends(obter_usuario_atual)
):
    if usuario_atual.get("papel") not in ["ADMIN", "MEDICO"]:
        raise HTTPException(status_code=403, detail="Acesso negado")

    leitos = db.query(m.Leito).all()
    registrar_log(db, usuario_atual["email"], "Leito", acao="READ", detalhes="Listagem de leitos")
    return leitos


# ----------------------------
# Atualizar leito
# ----------------------------
@roteador.put("/leitos/{leito_id}", response_model=LeitoResponse)
def atualizar_leito(
        leito_id: int,
        dados: LeitoBase,
        db: Session = Depends(get_db),
        usuario_atual=Depends(obter_usuario_atual)
):
    if usuario_atual.get("papel") != "ADMIN":
        raise HTTPException(status_code=403, detail="Acesso negado")

    leito = db.query(m.Leito).filter(m.Leito.id == leito_id).first()
    if not leito:
        raise HTTPException(status_code=404, detail="Leito não encontrado")

    leito.numero = dados.numero
    leito.status = dados.status
    leito.paciente_id = dados.paciente_id
    db.commit()
    db.refresh(leito)

    registrar_log(db, usuario_atual["email"], "Leito", leito.id, "UPDATE", f"Leito {leito_id} atualizado")
    return leito


# ----------------------------
# Remover leito
# ----------------------------
@roteador.delete("/leitos/{leito_id}")
def remover_leito(
        leito_id: int,
        db: Session = Depends(get_db),
        usuario_atual=Depends(obter_usuario_atual)
):
    if usuario_atual.get("papel") != "ADMIN":
        raise HTTPException(status_code=403, detail="Acesso negado")

    leito = db.query(m.Leito).filter(m.Leito.id == leito_id).first()
    if not leito:
        raise HTTPException(status_code=404, detail="Leito não encontrado")

    db.delete(leito)
    db.commit()

    registrar_log(db, usuario_atual["email"], "Leito", leito_id, "DELETE", f"Leito {leito_id} removido")
    return {"detail": "Leito removido com sucesso"}
