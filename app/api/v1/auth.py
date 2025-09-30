from fastapi import APIRouter, Depends, HTTPException, status, Body
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
        email: str = Body(...),
        password: str = Body(...),
        role: Optional[str] = Body(default="USER"),
        db: Session = Depends(get_db_session)
):
    if db.query(m.User).filter(m.User.email == email).first():
        raise HTTPException(status_code=400, detail="Email já cadastrado")

    hashed_password = security.hash_password(password)
    user = m.User(email=email, hashed_password=hashed_password, role=role)

    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "email": user.email, "role": user.role}


# ----------------------------
# Listar usuários (apenas ADMIN)
# ----------------------------
@router.get("/users")
def listar_usuarios(
        db: Session = Depends(get_db_session),
        current_user=Depends(security.get_current_user)
):
    if current_user.get("role") != "ADMIN":
        raise HTTPException(status_code=403, detail="Apenas administradores podem listar usuários")

    users = db.query(m.User).all()
    return [
        {
            "id": u.id,
            "email": u.email,
            "role": u.role,
            "active": u.active
        }
        for u in users
    ]


# ----------------------------
# Atualizar usuário (ADMIN)
# ----------------------------
@router.put("/users/{user_id}")
def update_user(
        user_id: int,
        email: str | None = Body(default=None),
        password: str | None = Body(default=None),
        role: str | None = Body(default=None),
        active: bool | None = Body(default=None),
        db: Session = Depends(get_db_session),
        current_user=Depends(security.get_current_user)
):
    if current_user.get("role") != "ADMIN":
        raise HTTPException(status_code=403, detail="Apenas administradores podem atualizar usuários")

    user = db.query(m.User).filter(m.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    if email:
        if db.query(m.User).filter(m.User.email == email, m.User.id != user.id).first():
            raise HTTPException(status_code=400, detail="Email já em uso")
        user.email = email

    if password:
        user.hashed_password = security.hash_password(password)

    if role:
        user.role = role

    if active is not None:
        user.active = active

    db.commit()
    db.refresh(user)

    return {
        "id": user.id,
        "email": user.email,
        "role": user.role,
        "active": user.active
    }


# ----------------------------
# Atualizar o próprio usuário (/me)
# ----------------------------
@router.put("/me")
def update_me(
        email: str | None = Body(default=None),
        password: str | None = Body(default=None),
        db: Session = Depends(get_db_session),
        current_user=Depends(security.get_current_user)
):
    user = db.query(m.User).filter(m.User.id == int(current_user["sub"])).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    if email:
        if db.query(m.User).filter(m.User.email == email, m.User.id != user.id).first():
            raise HTTPException(status_code=400, detail="Email já em uso")
        user.email = email

    if password:
        user.hashed_password = security.hash_password(password)

    db.commit()
    db.refresh(user)

    return {
        "id": user.id,
        "email": user.email,
        "role": user.role,
        "active": user.active
    }
