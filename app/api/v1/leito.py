# D:\ProjectSGHSS\app\api\v1\leito.py
from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db import get_db
from app import models as m
from app.core import security
from pydantic import BaseModel
from app.utils.logs import registrar_log


# ============================================================
# SCHEMAS
# ============================================================
class LeitoBase(BaseModel):
    """
    Schema base para criar ou atualizar um leito.
    """
    numero: str
    status: str
    paciente_id: Optional[int] = None


class LeitoResponse(LeitoBase):
    """
    Schema de resposta de um leito, incluindo o ID.
    Compatível com objetos SQLAlchemy (from_attributes=True).
    """
    id: int

    model_config = {"from_attributes": True}  # Pydantic v2


# ============================================================
# ROTEADOR
# ============================================================
roteador = APIRouter()


# ============================================================
# Função auxiliar: obter usuário autenticado
# ============================================================
def obter_usuario_atual(
        current_user=Depends(security.get_current_user),
        db: Session = Depends(get_db)
):
    """
    Obtém o usuário autenticado garantindo que o campo `email` esteja presente.
    """
    usuario_email = current_user.get("email")
    if not usuario_email:
        usuario = db.query(m.Usuario).filter(m.Usuario.id == int(current_user.get("id"))).first()
        if usuario:
            usuario_email = usuario.email
            current_user["email"] = usuario.email
    return current_user


# ============================================================
# Endpoint: CRIAR LEITO
# ============================================================
@roteador.post("/leitos", response_model=LeitoResponse, status_code=status.HTTP_201_CREATED)
def criar_leito(
        numero: str = Form(..., description="Número identificador do leito", example="101"),
        status_leito: str = Form(..., description="Status atual do leito (Livre, Ocupado, Manutenção)",
                                 example="Livre"),
        paciente_id: Optional[int] = Form(None, description="ID do paciente associado (opcional)"),
        db: Session = Depends(get_db),
        usuario_atual=Depends(obter_usuario_atual)
):
    """
    Cria um novo leito hospitalar.

    - **Acesso:** apenas ADMIN
    - **Campos obrigatórios:** numero, status
    - **Campos opcionais:** paciente_id
    """
    if usuario_atual.get("papel") != "ADMIN":
        raise HTTPException(status_code=403, detail="Acesso negado: apenas ADMIN pode criar leitos")

    novo_leito = m.Leito(numero=numero, status=status_leito, paciente_id=paciente_id)
    db.add(novo_leito)
    db.commit()
    db.refresh(novo_leito)

    registrar_log(
        db,
        usuario_atual["email"],
        "Leito",
        registro_id=novo_leito.id,
        acao="CREATE",
        detalhes=f"Leito {numero} criado com status {status_leito}"
    )

    return novo_leito


# ============================================================
# Endpoint: LISTAR LEITOS
# ============================================================
@roteador.get("/leitos", response_model=List[LeitoResponse])
def listar_leitos(
        db: Session = Depends(get_db),
        usuario_atual=Depends(obter_usuario_atual)
):
    """
    Lista todos os leitos cadastrados.

    - **Acesso:** ADMIN ou MEDICO
    """
    if usuario_atual.get("papel") not in ["ADMIN", "MEDICO"]:
        raise HTTPException(status_code=403, detail="Acesso negado")

    leitos = db.query(m.Leito).all()

    registrar_log(
        db,
        usuario_atual["email"],
        "Leito",
        acao="READ",
        detalhes="Listagem de leitos"
    )

    return leitos


# ============================================================
# Endpoint: ATUALIZAR LEITO (PATCH)
# ============================================================
@roteador.patch("/leitos/{leito_id}", response_model=LeitoResponse)
def atualizar_leito(
        leito_id: int,
        numero: Optional[str] = Form(None, description="Número identificador do leito", example="101"),
        status_leito: Optional[str] = Form(None, description="Status atual do leito", example="Livre"),
        paciente_id: Optional[int] = Form(None, description="ID do paciente associado", example=None),
        db: Session = Depends(get_db),
        usuario_atual=Depends(obter_usuario_atual)
):
    """
    Atualiza os campos de um leito existente.

    - **Acesso:** apenas ADMIN
    - **Campos opcionais:** numero, status, paciente_id
    """
    if usuario_atual.get("papel") != "ADMIN":
        raise HTTPException(status_code=403, detail="Acesso negado")

    leito = db.query(m.Leito).filter(m.Leito.id == leito_id).first()
    if not leito:
        raise HTTPException(status_code=404, detail="Leito não encontrado")

    if numero is not None:
        leito.numero = numero
    if status_leito is not None:
        leito.status = status_leito
    if paciente_id is not None:
        leito.paciente_id = paciente_id

    db.commit()
    db.refresh(leito)

    registrar_log(
        db,
        usuario_atual["email"],
        "Leito",
        registro_id=leito.id,
        acao="UPDATE",
        detalhes=f"Leito {leito_id} atualizado"
    )

    return leito


# ============================================================
# Endpoint: REMOVER LEITO
# ============================================================
@roteador.delete("/leitos/{leito_id}")
def remover_leito(
        leito_id: int,
        db: Session = Depends(get_db),
        usuario_atual=Depends(obter_usuario_atual)
):
    """
    Remove um leito pelo ID.

    - **Acesso:** apenas ADMIN
    """
    if usuario_atual.get("papel") != "ADMIN":
        raise HTTPException(status_code=403, detail="Acesso negado")

    leito = db.query(m.Leito).filter(m.Leito.id == leito_id).first()
    if not leito:
        raise HTTPException(status_code=404, detail="Leito não encontrado")

    db.delete(leito)
    db.commit()

    registrar_log(
        db,
        usuario_atual["email"],
        "Leito",
        registro_id=leito_id,
        acao="DELETE",
        detalhes=f"Leito {leito_id} removido"
    )

    return {"detail": "Leito removido com sucesso"}
