# app/api/v1/auth.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Optional
from datetime import timedelta

from app.db import get_db_session
from app import models as m
from app.core import security

router = APIRouter()


# ----------------------------
# Login - retorna JWT
# ----------------------------
@router.post("/login")
def login(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: Session = Depends(get_db_session)
):
    user = db.query(m.User).filter(m.User.email == form_data.username).first()
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Email ou senha inválidos")

    if not user.active:
        raise HTTPException(status_code=403, detail="Usuário inativo")

    # Inclui id (sub) e role no token
    token_data = {"sub": str(user.id), "role": user.role}
    access_token = security.create_access_token(token_data, expires_delta=timedelta(hours=1))

    return {"access_token": access_token, "token_type": "bearer", "role": user.role}


# ----------------------------
# Registrar usuário
# ----------------------------
@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(
        email: str,
        password: str,
        role: Optional[str] = "PATIENT",
        db: Session = Depends(get_db_session),
        current_user=Depends(security.get_current_user)
):
    # Verifica se já existe usuário com este email
    if db.query(m.User).filter(m.User.email == email).first():
        raise HTTPException(status_code=400, detail="Email já cadastrado")

    # Se o usuário tentar criar PROFESSIONAL ou ADMIN
    if role in ["PROFESSIONAL", "ADMIN"]:
        if not current_user or current_user.get("role") != "ADMIN":
            raise HTTPException(status_code=403, detail="Apenas ADMIN pode criar usuários PROFESSIONAL ou ADMIN")

    # Sempre força PATIENT para usuários comuns
    if role not in ["PATIENT", "PROFESSIONAL", "ADMIN"]:
        role = "PATIENT"

    hashed_password = security.hash_password(password)
    user = m.User(email=email, hashed_password=hashed_password, role=role)

    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "email": user.email, "role": user.role}


# ----------------------------
# Listar todos os usuários (somente ADMIN)
# ----------------------------
@router.get("/users")
def listar_usuarios(
        current_user=Depends(security.get_current_user),
        db: Session = Depends(get_db_session)
):
    if current_user.get("role") != "ADMIN":
        raise HTTPException(status_code=403, detail="Acesso negado: apenas ADMIN pode listar usuários")

    usuarios = db.query(m.User).all()
    return [
        {
            "id": u.id,
            "email": u.email,
            "role": u.role,
            "active": u.active,
            "created_at": u.created_at
        }
        for u in usuarios
    ]


# ----------------------------
# Dados do usuário logado
# ----------------------------
@router.get("/me")
def get_me(current_user=Depends(security.get_current_user), db: Session = Depends(get_db_session)):
    user = db.query(m.User).filter(m.User.id == current_user.get("sub")).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    return {
        "id": user.id,
        "email": user.email,
        "role": user.role,
        "active": user.active,
        "created_at": user.created_at
    }
