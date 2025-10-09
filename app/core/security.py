# D:\ProjectSGHSS\app\core\security.py
from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from datetime import datetime, timedelta
from app.db import get_db_session
from app import models as m
import os
import bcrypt

# -------------------------------
# Configurações do Token JWT
# -------------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "CHAVE_SUPER_SECRETA_PADRAO")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_HOURS = int(os.getenv("ACCESS_TOKEN_EXPIRE_HOURS", 8))

# Esquema de autenticação OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/autenticacao/login")


# -------------------------------
# Funções de Senha (bcrypt)
# -------------------------------
def hash_password(password: str) -> str:
    """Gera o hash da senha usando bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se a senha informada corresponde ao hash armazenado."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


# -------------------------------
# Geração do Token JWT
# -------------------------------
def create_access_token(data: dict, expires_delta: timedelta = timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)):
    """Cria um token JWT com tempo de expiração."""
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})

    # Adiciona "sub" (identificador padrão do usuário)
    if "email" in to_encode:
        to_encode["sub"] = to_encode["email"]

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# -------------------------------
# Obtém o usuário logado (via cookie ou header)
# -------------------------------
def get_current_user(request: Request, db=Depends(get_db_session)):
    """Obtém o usuário autenticado a partir do token JWT."""
    token = None

    # Tenta pegar o token do cookie primeiro
    if "access_token" in request.cookies:
        token = request.cookies.get("access_token")
    else:
        # Se não houver cookie, tenta pegar do header Authorization
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

    if not token:
        raise HTTPException(status_code=401, detail="Token de acesso ausente")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Token inválido")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

    usuario = db.query(m.Usuario).filter(m.Usuario.email == email).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    # ✅ Corrigido: campo 'papel' no lugar de 'role', já retorna o valor do Enum
    return {"id": usuario.id, "email": usuario.email, "papel": usuario.papel.value}
