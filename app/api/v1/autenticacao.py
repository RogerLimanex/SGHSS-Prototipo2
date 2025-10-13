# D:\ProjectSGHSS\app\api\v1\autenticacao.py
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
# 📘 Schema para Login
# ----------------------------
class LoginSchema(BaseModel):
    """Esquema Pydantic para validação de dados de login"""
    username: str
    password: str


# ----------------------------
# 🔐 Obter usuário atual com email garantido
# ----------------------------
def obter_usuario_atual(
        current_user=Depends(security.get_current_user),
        db: Session = Depends(get_db)
):
    """
    🔐 **Obter Usuário Atual**

    Garante que o usuário autenticado tenha o campo `email` disponível.
    Caso o token JWT não contenha o e-mail, ele é recuperado do banco de dados.

    Retorna:
        dict: Dados do usuário autenticado (com campo `email` garantido).
    """
    email = current_user.get("email")

    # Recupera o email do banco se não estiver no token
    if not email:
        usuario = db.query(m.Usuario).filter(m.Usuario.id == int(current_user.get("id"))).first()
        if usuario:
            email = usuario.email
            current_user["email"] = email
    return current_user


# ----------------------------
# 🔑 Login - retorna JWT e grava cookie
# ----------------------------
@roteador.post("/login")
def login(
        response: Response,
        username: str = Form(..., description="Email do usuário"),
        password: str = Form(..., description="Senha do usuário"),
        db: Session = Depends(get_db)
):
    """
    🔑 **Login de Usuário**

    Autentica um usuário com **email e senha**, gera um **token JWT** e grava um cookie HTTP-only
    contendo o token de acesso.

    Retorno:
    * `access_token`: Token de acesso JWT
    * `token_type`: Tipo de autenticação
    * `id`, `email`, `papel`: Dados do usuário autenticado
    """
    # Busca o usuário pelo e-mail informado
    usuario = db.query(m.Usuario).filter(m.Usuario.email == username).first()

    # Validações básicas
    if not usuario or not security.verify_password(password, usuario.hashed_password):
        raise HTTPException(status_code=401, detail="Email ou senha inválidos")
    if not usuario.ativo:
        raise HTTPException(status_code=403, detail="Usuário inativo")

    # Geração do token de acesso
    token_data = {
        "id": usuario.id,
        "email": usuario.email,
        "papel": usuario.papel.value if hasattr(usuario.papel, "value") else usuario.papel
    }
    access_token = security.create_access_token(token_data, expires_delta=timedelta(hours=1))

    # Criação da resposta JSON com o token
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

    # Grava cookie seguro (não acessível via JS)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=3600,
        samesite="lax",
        secure=False
    )

    # Registra o log de login
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
# 🚪 Logout - remove cookie de autenticação
# ----------------------------
@roteador.post("/logout")
def logout(response: Response):
    """
    🚪 **Logout de Usuário**

    Remove o cookie `access_token` do navegador, encerrando a sessão atual.
    """
    response = JSONResponse(content={"message": "Logout realizado com sucesso"})
    response.delete_cookie("access_token")
    return response


# ----------------------------
# 🧾 Registrar novo usuário
# ----------------------------
@roteador.post("/register", status_code=status.HTTP_201_CREATED)
def registrar(
        email: str = Form(..., description="Email do novo usuário"),
        password: str = Form(..., description="Senha do novo usuário"),
        papel: Optional[str] = Form("PACIENTE", description="Papel do usuário: PACIENTE, MEDICO ou ADMIN"),
        db: Session = Depends(get_db),
        current_user=Depends(obter_usuario_atual)
):
    """
    🧾 **Registrar Novo Usuário**

    Cria um novo usuário no sistema.
    - Usuários **ADMIN** podem criar qualquer tipo (PACIENTE, MÉDICO, ADMIN).
    - Usuários comuns só podem criar PACIENTES.

    Campos esperados:
    * `email`: Endereço de e-mail único
    * `password`: Senha do usuário
    * `papel`: Tipo de usuário (PACIENTE, MEDICO, ADMIN)
    """
    # Impede duplicidade de email
    if db.query(m.Usuario).filter(m.Usuario.email == email).first():
        raise HTTPException(status_code=400, detail="Email já cadastrado")

    # Restringe criação de usuários especiais
    if papel in ["MEDICO", "ADMIN"] and (not current_user or current_user.get("papel") != "ADMIN"):
        raise HTTPException(status_code=403, detail="Apenas ADMIN pode criar usuários MEDICO ou ADMIN")

    # Define papel padrão caso inválido
    if papel not in ["PACIENTE", "MEDICO", "ADMIN"]:
        papel = "PACIENTE"

    # Criptografa a senha e salva o novo usuário
    hashed_password = security.hash_password(password)
    usuario = m.Usuario(email=email, hashed_password=hashed_password, papel=papel)

    db.add(usuario)
    db.commit()
    db.refresh(usuario)

    # Identifica quem criou o usuário (ou "sistema" se automático)
    criador_email = "sistema"
    if current_user:
        criador = db.query(m.Usuario).filter(m.Usuario.id == int(current_user.get("id"))).first()
        criador_email = criador.email if criador else "sistema"

    # Log de criação
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
# 👥 Listar todos os usuários (somente ADMIN)
# ----------------------------
@roteador.get("/usuarios")
def listar_usuarios(
        current_user=Depends(obter_usuario_atual),
        db: Session = Depends(get_db)
):
    """
    👥 **Listar Todos os Usuários**

    Exibe todos os usuários cadastrados no sistema.

    **Acesso:** Somente ADMIN.

    Campos retornados:
    * `id`
    * `email`
    * `papel`
    * `ativo`
    * `criado_em`
    """
    if current_user.get("papel") != "ADMIN":
        raise HTTPException(status_code=403, detail="Acesso negado: apenas ADMIN")

    usuarios = db.query(m.Usuario).all()
    admin_email = current_user.get("email") or "desconhecido"

    # Registra log da leitura
    registrar_log(
        db=db,
        usuario_email=admin_email,
        tabela="usuarios",
        registro_id=None,
        acao="READ",
        detalhes=f"Usuário {admin_email} listou todos os usuários"
    )

    # Retorna a lista formatada
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
# 🙋‍♂️ Dados do usuário logado
# ----------------------------
@roteador.get("/me")
def obter_me(
        current_user=Depends(obter_usuario_atual),
        db: Session = Depends(get_db)
):
    """
    🙋‍♂️ **Obter Dados do Usuário Logado**

    Retorna os dados do usuário atualmente autenticado.

    Campos retornados:
    * `id`
    * `email`
    * `papel`
    * `ativo`
    * `criado_em`
    """
    usuario = db.query(m.Usuario).filter(m.Usuario.id == int(current_user.get("id"))).first()

    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    # Loga o acesso do próprio usuário às suas informações
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
