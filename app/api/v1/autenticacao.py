# D:\ProjectSGHSS\app\api\v1\autenticacao.py
from fastapi import APIRouter, Depends, HTTPException, status, Form
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
# Login - retorna JWT
# ----------------------------
@roteador.post("/login")
def login(
        username: str = Form(..., description="Email do usuário"),
        password: str = Form(..., description="Senha do usuário"),
        db: Session = Depends(get_db_session)
):
    usuario = db.query(m.Usuario).filter(m.Usuario.email == username).first()
    if not usuario or not security.verify_password(password, usuario.hashed_password):
        raise HTTPException(status_code=401, detail="Email ou senha inválidos")

    if not usuario.ativo:
        raise HTTPException(status_code=403, detail="Usuário inativo")

    # Monta dados do token JWT
    token_data = {
        "id": usuario.id,
        "email": usuario.email,
        "role": usuario.papel.value if hasattr(usuario.papel, 'value') else usuario.papel
    }

    access_token = security.create_access_token(token_data, expires_delta=timedelta(hours=1))

    # Log de login
    registrar_log(
        db=db,
        usuario_email=usuario.email,
        tabela="Usuario",
        registro_id=usuario.id,
        acao="LOGIN",
        detalhes=f"Usuário {usuario.email} realizou login"
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "id": usuario.id,
        "email": usuario.email,
        "role": usuario.papel
    }


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
    if db.query(m.Usuario).filter(m.Usuario.email == email).first():
        raise HTTPException(status_code=400, detail="Email já cadastrado")

    # Somente ADMIN pode criar MEDICO ou ADMIN
    if papel in ["MEDICO", "ADMIN"]:
        if not current_user or current_user.get("role") != "ADMIN":
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

    # Log de criação de usuário
    registrar_log(
        db=db,
        usuario_email=criador_email,
        tabela="Usuario",
        registro_id=usuario.id,
        acao="CREATE",
        detalhes=f"Usuário {usuario.email} criado com papel {papel}"
    )

    return {"id": usuario.id, "email": usuario.email, "role": usuario.papel}


# ----------------------------
# Listar todos os usuários (ADMIN)
# ----------------------------
@roteador.get("/usuarios")
def listar_usuarios(
        current_user=Depends(security.get_current_user),
        db: Session = Depends(get_db_session)
):
    if current_user.get("role") != "ADMIN":
        raise HTTPException(status_code=403, detail="Acesso negado: apenas ADMIN")

    usuarios = db.query(m.Usuario).all()

    admin_email = current_user.get("email") or "desconhecido"

    # Log de listagem
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
            "role": u.papel,
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
    usuario = db.query(m.Usuario).filter(m.Usuario.id == int(current_user.get("id"))).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    # Log de acesso a dados próprios
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
        "role": usuario.papel,
        "ativo": usuario.ativo,
        "criado_em": usuario.criado_em
    }
