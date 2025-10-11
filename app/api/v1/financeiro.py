# D:\ProjectSGHSS\app\api\v1\financeiro.py
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
from app.db import get_db
from app import models as m
from app.core import security
from app.schemas.financeiro import FinanceiroBase, FinanceiroResponse, ResumoFinanceiroResponse
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
# Registrar movimentação financeira
# ----------------------------
@roteador.post("/financeiro", response_model=FinanceiroResponse, status_code=status.HTTP_201_CREATED)
def registrar_movimento(
        movimento: FinanceiroBase,
        db: Session = Depends(get_db),
        usuario_atual=Depends(obter_usuario_atual)
):
    if usuario_atual.get("papel") != "ADMIN":
        raise HTTPException(status_code=403, detail="Acesso negado: apenas ADMIN")

    novo = m.Financeiro(
        tipo=movimento.tipo,
        descricao=movimento.descricao,
        valor=movimento.valor,
        data_registro=datetime.now()
    )
    db.add(novo)
    db.commit()
    db.refresh(novo)

    registrar_log(db, usuario_atual["email"], "Financeiro", novo.id, "CREATE",
                  f"Movimentação {movimento.tipo} registrada: {movimento.descricao}")

    return novo


# ----------------------------
# Listar movimentações financeiras
# ----------------------------
@roteador.get("/financeiro", response_model=List[FinanceiroResponse])
def listar_movimentos(
        tipo: Optional[str] = None,
        data_inicial: Optional[date] = None,
        data_final: Optional[date] = None,
        db: Session = Depends(get_db),
        usuario_atual=Depends(obter_usuario_atual)
):
    if usuario_atual.get("papel") != "ADMIN":
        raise HTTPException(status_code=403, detail="Acesso negado: apenas ADMIN")

    query = db.query(m.Financeiro)
    if tipo:
        query = query.filter(m.Financeiro.tipo == tipo.upper())
    if data_inicial and data_final:
        query = query.filter(m.Financeiro.data_registro.between(data_inicial, data_final))

    lista = query.all()

    registrar_log(db, usuario_atual["email"], "Financeiro", acao="READ",
                  detalhes="Listagem de movimentações financeiras")

    return lista


# ----------------------------
# Gerar resumo financeiro
# ----------------------------
@roteador.get("/financeiro/resumo", response_model=ResumoFinanceiroResponse)
def gerar_resumo(
        db: Session = Depends(get_db),
        usuario_atual=Depends(obter_usuario_atual)
):
    if usuario_atual.get("papel") != "ADMIN":
        raise HTTPException(status_code=403, detail="Acesso negado: apenas ADMIN")

    entradas = db.query(m.Financeiro).filter(m.Financeiro.tipo == "ENTRADA").all()
    saidas = db.query(m.Financeiro).filter(m.Financeiro.tipo == "SAIDA").all()

    total_entradas = sum(e.valor for e in entradas)
    total_saidas = sum(s.valor for s in saidas)
    saldo = total_entradas - total_saidas

    registrar_log(db, usuario_atual["email"], "Financeiro", acao="READ",
                  detalhes="Resumo financeiro gerado")

    return ResumoFinanceiroResponse(
        total_entradas=total_entradas,
        total_saidas=total_saidas,
        saldo=saldo
    )
