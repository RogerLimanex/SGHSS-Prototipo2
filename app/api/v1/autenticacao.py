from fastapi import APIRouter, Depends, HTTPException, status, Form, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import timedelta
from pydantic import BaseModel

from app.db import get_db
from app import models as m
from app.core import security
from app.utils.logs import registrar_log

roteador = APIRouter()


# ----------------------------
# Schema para login
# ----------------------------
class LoginSchema(BaseModel):
    username: str
    password: str


# ----------------------------
# Obter usuário atual com email garantido
# ----------------------------
def obter_usuario_atual(
        current_user=Depends(security.get_current_user),
        db: Session = Depends(get_db)
):
    email = current_user.get("email")
    if not email:
        usuario = db.query(m.Usuario).filter(m.Usuario.id == int(current_user.get("id"))).first()
        if usuario:
            email = usuario.email
            current_user["email"] = email
    return current_user


# ----------------------------
# Login - retorna JWT e grava cookie
# ----------------------------
@roteador.post("/login")
def login(
        response: Response,
        username: str = Form(..., description="Email do usuário"),
        password: str = Form(..., description="Senha do usuário"),
        db: Session = Depends(get_db)
):
    usuario = db.query(m.Usuario).filter(m.Usuario.email == username).first()
    if not usuario or not security.verify_password(password, usuario.hashed_password):
        raise HTTPException(status_code=401, detail="Email ou senha inválidos")
    if not usuario.ativo:
        raise HTTPException(status_code=403, detail="Usuário inativo")

    token_data = {
        "id": usuario.id,
        "email": usuario.email,
        "papel": usuario.papel.value if hasattr(usuario.papel, "value") else usuario.papel
    }

    access_token = security.create_access_token(token_data, expires_delta=timedelta(hours=1))

    response = JSONResponse(
        content={
            "message": "Login realizado com sucesso",
            "access_token": access_token,
            "token_type": "bearer",
            "id": usuario.id,
            "email": usuario.email,
            "papel": usuario.papel
        }
    )
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=3600,
        samesite="lax",
        secure=False
    )

    registrar_log(
        db=db,
        usuario_email=usuario.email,
        tabela="usuarios",
        registro_id=usuario.id,
        acao="LOGIN",
        detalhes=f"Usuário {usuario.email} realizou login"
    )

    return response


# ----------------------------
# Logout - remove cookie
# ----------------------------
@roteador.post("/logout")
def logout(response: Response):
    response = JSONResponse(content={"message": "Logout realizado com sucesso"})
    response.delete_cookie("access_token")
    return response


# ----------------------------
# Registrar usuário
# ----------------------------
@roteador.post("/register", status_code=status.HTTP_201_CREATED)
def registrar(
        email: str = Form(...),
        password: str = Form(...),
        papel: Optional[str] = Form("PACIENTE"),
        db: Session = Depends(get_db),
        current_user=Depends(obter_usuario_atual)
):
    if db.query(m.Usuario).filter(m.Usuario.email == email).first():
        raise HTTPException(status_code=400, detail="Email já cadastrado")

    if papel in ["MEDICO", "ADMIN"] and (not current_user or current_user.get("papel") != "ADMIN"):
        raise HTTPException(status_code=403, detail="Apenas ADMIN pode criar usuários MEDICO ou ADMIN")

    if papel not in ["PACIENTE", "MEDICO", "ADMIN"]:
        papel = "PACIENTE"

    hashed_password = security.hash_password(password)
    usuario = m.Usuario(email=email, hashed_password=hashed_password, papel=papel)

    db.add(usuario)
    db.commit()
    db.refresh(usuario)

    criador_email = "sistema"
    if current_user:
        criador = db.query(m.Usuario).filter(m.Usuario.id == int(current_user.get("id"))).first()
        criador_email = criador.email if criador else "sistema"

    registrar_log(
        db=db,
        usuario_email=criador_email,
        tabela="usuarios",
        registro_id=usuario.id,
        acao="CREATE",
        detalhes=f"Usuário {usuario.email} criado com papel {papel}"
    )

    return {"id": usuario.id, "email": usuario.email, "papel": usuario.papel}


# ----------------------------
# Listar todos os usuários (ADMIN)
# ----------------------------
@roteador.get("/usuarios")
def listar_usuarios(
        current_user=Depends(obter_usuario_atual),
        db: Session = Depends(get_db)
):
    if current_user.get("papel") != "ADMIN":
        raise HTTPException(status_code=403, detail="Acesso negado: apenas ADMIN")

    usuarios = db.query(m.Usuario).all()
    admin_email = current_user.get("email") or "desconhecido"

    registrar_log(
        db=db,
        usuario_email=admin_email,
        tabela="usuarios",
        registro_id=None,
        acao="READ",
        detalhes=f"Usuário {admin_email} listou todos os usuários"
    )

    return [
        {
            "id": u.id,
            "email": u.email,
            "papel": u.papel,
            "ativo": u.ativo,
            "criado_em": u.criado_em
        } for u in usuarios
    ]


# ----------------------------
# Dados do usuário logado
# ----------------------------
@roteador.get("/me")
def obter_me(
        current_user=Depends(obter_usuario_atual),
        db: Session = Depends(get_db)
):
    usuario = db.query(m.Usuario).filter(m.Usuario.id == int(current_user.get("id"))).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    registrar_log(
        db=db,
        usuario_email=usuario.email,
        tabela="usuarios",
        registro_id=usuario.id,
        acao="READ",
        detalhes=f"Usuário {usuario.email} acessou seus dados"
    )

    return {
        "id": usuario.id,
        "email": usuario.email,
        "papel": usuario.papel,
        "ativo": usuario.ativo,
        "criado_em": usuario.criado_em
    }
