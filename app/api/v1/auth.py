from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Optional
from datetime import timedelta

from app.db import get_db_session
from app import models as m
from app.core import security

roteador = APIRouter()


# ----------------------------
# Login - retorna JWT
# ----------------------------
@roteador.post("/login")
def login(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: Session = Depends(get_db_session)
):
    usuario = db.query(m.Usuario).filter(m.Usuario.email == form_data.username).first()
    if not usuario or not security.verify_password(form_data.password, usuario.hashed_password):
        raise HTTPException(status_code=401, detail="Email ou senha inválidos")

    if not usuario.ativo:
        raise HTTPException(status_code=403, detail="Usuário inativo")

    # Inclui id (sub) e role no token
    token_data = {"sub": str(usuario.id),
                  "role": usuario.papel.value if hasattr(usuario.papel, 'value') else usuario.papel}
    access_token = security.create_access_token(token_data, expires_delta=timedelta(hours=1))

    return {"access_token": access_token, "token_type": "bearer", "role": usuario.papel}


# ----------------------------
# Registrar usuário
# ----------------------------
@roteador.post("/register", status_code=status.HTTP_201_CREATED)
def registrar(
        email: str,
        password: str,
        papel: Optional[str] = "PACIENTE",
        db: Session = Depends(get_db_session),
        current_user=Depends(security.get_current_user)
):
    # Verifica se já existe usuário com este email
    if db.query(m.Usuario).filter(m.Usuario.email == email).first():
        raise HTTPException(status_code=400, detail="Email já cadastrado")

    # Apenas ADMIN pode criar MEDICO ou ADMIN
    if papel in ["MEDICO", "ADMIN"]:
        if not current_user or current_user.get("role") != "ADMIN":
            raise HTTPException(status_code=403, detail="Apenas ADMIN pode criar usuários MEDICO ou ADMIN")

    # Força PACIENTE como default para usuários comuns
    if papel not in ["PACIENTE", "MEDICO", "ADMIN"]:
        papel = "PACIENTE"

    hashed_password = security.hash_password(password)
    usuario = m.Usuario(email=email, hashed_password=hashed_password, papel=papel)

    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return {"id": usuario.id, "email": usuario.email, "role": usuario.papel}


# ----------------------------
# Listar todos os usuários (somente ADMIN)
# ----------------------------
@roteador.get("/users")
def listar_usuarios(
        current_user=Depends(security.get_current_user),
        db: Session = Depends(get_db_session)
):
    if current_user.get("role") != "ADMIN":
        raise HTTPException(status_code=403, detail="Acesso negado: apenas ADMIN pode listar usuários")

    usuarios = db.query(m.Usuario).all()
    return [
        {
            "id": u.id,
            "email": u.email,
            "role": u.papel,
            "active": u.ativo,
            "created_at": u.criado_em
        }
        for u in usuarios
    ]


# ----------------------------
# Dados do usuário logado
# ----------------------------
@roteador.get("/me")
def obter_me(current_user=Depends(security.get_current_user), db: Session = Depends(get_db_session)):
    usuario = db.query(m.Usuario).filter(m.Usuario.id == int(current_user.get("sub"))).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    return {
        "id": usuario.id,
        "email": usuario.email,
        "role": usuario.papel,
        "active": usuario.ativo,
        "created_at": usuario.criado_em
    }
