# D:\ProjectSGHSS\app\api\v1\autenticacao.py
from fastapi import APIRouter, Depends, HTTPException, status, Form, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import timedelta
from pydantic import BaseModel

from app.db import get_db_session
from app import models as m
from app.core import security
from app.utils.logs import registrar_log  # Função util para logs

roteador = APIRouter()


# ----------------------------
# Schema para login
# ----------------------------
class LoginSchema(BaseModel):
    username: str
    password: str


# ----------------------------
# Login - retorna JWT e grava cookie
# ----------------------------
@roteador.post("/login")
def login(
        response: Response,
        username: str = Form(..., description="Email do usuário"),
        password: str = Form(..., description="Senha do usuário"),
        db: Session = Depends(get_db_session)
):
    """Autentica o usuário e grava o token JWT em cookie HTTPOnly."""
    usuario = db.query(m.Usuario).filter(m.Usuario.email == username).first()
    if not usuario or not security.verify_password(password, usuario.hashed_password):
        raise HTTPException(status_code=401, detail="Email ou senha inválidos")

    if not usuario.ativo:
        raise HTTPException(status_code=403, detail="Usuário inativo")

    # Monta payload do token JWT
    token_data = {
        "id": usuario.id,
        "email": usuario.email,
        "papel": usuario.papel.value if hasattr(usuario.papel, "value") else usuario.papel
    }

    # Gera o token
    access_token = security.create_access_token(token_data, expires_delta=timedelta(hours=1))

    # Grava cookie HTTPOnly (seguro e persistente)
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
        secure=False  # Em produção, defina True (HTTPS)
    )

    # Log de login
    registrar_log(
        db=db,
        usuario_email=usuario.email,
        tabela="Usuario",
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
    """Remove o cookie de autenticação."""
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
        db: Session = Depends(get_db_session),
        current_user=Depends(security.get_current_user)
):
    """Cria um novo usuário (ADMIN pode criar qualquer tipo, outros só PACIENTE)."""
    if db.query(m.Usuario).filter(m.Usuario.email == email).first():
        raise HTTPException(status_code=400, detail="Email já cadastrado")

    # Somente ADMIN pode criar MEDICO ou ADMIN
    if papel in ["MEDICO", "ADMIN"]:
        if not current_user or current_user.get("papel") != "ADMIN":
            raise HTTPException(status_code=403, detail="Apenas ADMIN pode criar usuários MEDICO ou ADMIN")

    if papel not in ["PACIENTE", "MEDICO", "ADMIN"]:
        papel = "PACIENTE"

    hashed_password = security.hash_password(password)
    usuario = m.Usuario(email=email, hashed_password=hashed_password, papel=papel)

    db.add(usuario)
    db.commit()
    db.refresh(usuario)

    # Email do criador (ou "sistema" se não houver)
    criador_email = "sistema"
    if current_user:
        criador = db.query(m.Usuario).filter(m.Usuario.id == int(current_user.get("id"))).first()
        criador_email = criador.email if criador else "sistema"

    # Log de criação
    registrar_log(
        db=db,
        usuario_email=criador_email,
        tabela="Usuario",
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
        current_user=Depends(security.get_current_user),
        db: Session = Depends(get_db_session)
):
    """Lista todos os usuários (somente ADMIN)."""
    if current_user.get("papel") != "ADMIN":
        raise HTTPException(status_code=403, detail="Acesso negado: apenas ADMIN")

    usuarios = db.query(m.Usuario).all()
    admin_email = current_user.get("email") or "desconhecido"

    registrar_log(
        db=db,
        usuario_email=admin_email,
        tabela="Usuario",
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
        }
        for u in usuarios
    ]


# ----------------------------
# Dados do usuário logado
# ----------------------------
@roteador.get("/me")
def obter_me(
        current_user=Depends(security.get_current_user),
        db: Session = Depends(get_db_session)
):
    """Retorna os dados do usuário autenticado."""
    usuario = db.query(m.Usuario).filter(m.Usuario.id == int(current_user.get("id"))).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    registrar_log(
        db=db,
        usuario_email=usuario.email,
        tabela="Usuario",
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
