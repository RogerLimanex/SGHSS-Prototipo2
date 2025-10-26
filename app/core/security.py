from fastapi import Depends, HTTPException, Request  # Dependências FastAPI
from fastapi.security import OAuth2PasswordBearer  # OAuth2
from jose import jwt, JWTError  # JWT
from datetime import datetime, timedelta  # Datas
from app.db import get_db  # Sessão do banco
from app import models as m  # Models
import os  # Variáveis de ambiente
import bcrypt  # Hash de senhas

# -------------------------------
# Configurações do Token JWT
# -------------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "CHAVE_SUPER_SECRETA_PADRAO")  # Chave secreta
ALGORITHM = os.getenv("ALGORITHM", "HS256")  # Algoritmo JWT
ACCESS_TOKEN_EXPIRE_HOURS = int(os.getenv("ACCESS_TOKEN_EXPIRE_HOURS", 8))  # Expiração

# Esquema OAuth2 para login
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/autenticacao/login")


# -------------------------------
# Funções de Senha (bcrypt)
# -------------------------------
def hash_password(password: str) -> str:
    """Gera o hash da senha usando bcrypt."""
    salt = bcrypt.gensalt()  # Gera salt aleatório
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)  # Criptografa senha
    return hashed.decode("utf-8")  # Retorna string


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
    to_encode.update({"exp": expire})  # Adiciona expiração

    # Adiciona "sub" (identificador padrão do usuário)
    if "email" in to_encode:
        to_encode["sub"] = to_encode["email"]

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)  # Gera token
    return encoded_jwt


# -------------------------------
# Obtém o usuário logado (via cookie ou header)
# -------------------------------
def get_current_user(request: Request, db=Depends(get_db)):
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
