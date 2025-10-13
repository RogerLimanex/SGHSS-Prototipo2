# D:\ProjectSGHSS\app\api\v1\financeiro.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
from app.db import get_db
from app import models as m
from app.core import security
from app.schemas.financeiro import FinanceiroResponse, ResumoFinanceiroResponse
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
        tipo: str,
        descricao: str,
        valor: float,
        db: Session = Depends(get_db),
        usuario_atual=Depends(obter_usuario_atual)
):
    """
    📘 Registrar uma nova movimentação financeira.

    - **tipo**: ENTRADA ou SAIDA
    - **descricao**: texto descritivo da movimentação
    - **valor**: valor numérico da operação
    """
    if usuario_atual.get("papel") != "ADMIN":
        raise HTTPException(status_code=403, detail="Acesso negado: apenas ADMIN")

    tipo_upper = tipo.upper()
    if tipo_upper not in ["ENTRADA", "SAIDA"]:
        raise HTTPException(status_code=400, detail="Tipo deve ser ENTRADA ou SAIDA")

    novo = m.Financeiro(
        tipo=tipo_upper,
        descricao=descricao,
        valor=valor,
        data_registro=datetime.now()
    )

    db.add(novo)
    db.commit()
    db.refresh(novo)

    # Log detalhado
    registrar_log(
        db=db,
        usuario_email=usuario_atual["email"],
        categoria="Financeiro",
        registro_id=novo.id,
        acao="CREATE",
        detalhes=f"Movimentação '{tipo_upper}' registrada: {descricao} | Valor: {valor:.2f}"
    )

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
    """
    📋 Listar movimentações financeiras, com filtros opcionais:
    - **tipo** (ENTRADA/SAIDA)
    - **data_inicial** e **data_final**
    """
    if usuario_atual.get("papel") != "ADMIN":
        raise HTTPException(status_code=403, detail="Acesso negado: apenas ADMIN")

    query = db.query(m.Financeiro)
    if tipo:
        query = query.filter(m.Financeiro.tipo == tipo.upper())
    if data_inicial and data_final:
        query = query.filter(m.Financeiro.data_registro.between(data_inicial, data_final))

    lista = query.all()

    # Log padronizado
    registrar_log(
        db=db,
        usuario_email=usuario_atual["email"],
        categoria="Financeiro",
        acao="READ",
        detalhes=f"Listagem de movimentações | Tipo: {tipo or 'TODOS'} | "
                 f"Período: {data_inicial or '-'} até {data_final or '-'}"
    )

    return lista


# ----------------------------
# Gerar resumo financeiro
# ----------------------------
@roteador.get("/financeiro/resumo", response_model=ResumoFinanceiroResponse)
def gerar_resumo(
        db: Session = Depends(get_db),
        usuario_atual=Depends(obter_usuario_atual)
):
    """
    💰 Gera um resumo das movimentações financeiras:
    - Total de entradas
    - Total de saídas
    - Saldo atual
    """
    if usuario_atual.get("papel") != "ADMIN":
        raise HTTPException(status_code=403, detail="Acesso negado: apenas ADMIN")

    entradas = db.query(m.Financeiro).filter(m.Financeiro.tipo == "ENTRADA").all()
    saidas = db.query(m.Financeiro).filter(m.Financeiro.tipo == "SAIDA").all()

    total_entradas = sum(e.valor for e in entradas)
    total_saidas = sum(s.valor for s in saidas)
    saldo = total_entradas - total_saidas

    # Log padronizado
    registrar_log(
        db=db,
        usuario_email=usuario_atual["email"],
        categoria="Financeiro",
        acao="READ",
        detalhes=(
            f"Resumo financeiro gerado | Entradas: {total_entradas:.2f} | "
            f"Saídas: {total_saidas:.2f} | Saldo: {saldo:.2f}"
        )
    )

    return ResumoFinanceiroResponse(
        total_entradas=total_entradas,
        total_saidas=total_saidas,
        saldo=saldo
    )
