# D:\ProjectSGHSS\app\core\security.py
import os
from datetime import datetime, timedelta
import bcrypt
from jose import jwt, JWTError
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# ----------------------------
# Configurações de segurança
# ----------------------------
JWT_SECRET = os.getenv("JWT_SECRET", "CHANGE_ME")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

security_scheme = HTTPBearer()


# ----------------------------
# Funções de senha usando bcrypt
# ----------------------------
def hash_password(password: str) -> str:
    """Gera o hash da senha usando bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verifica se a senha informada corresponde ao hash armazenado."""
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


# ----------------------------
# Funções de token JWT
# ----------------------------
def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Cria um token JWT contendo id, email e role do usuário.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})

    # Garantir que sempre tenha 'id', 'email' e 'role' no token
    if "id" not in to_encode:
        raise ValueError("O token precisa do 'id' do usuário")
    if "email" not in to_encode:
        raise ValueError("O token precisa do 'email' do usuário")
    if "role" not in to_encode:
        raise ValueError("O token precisa do 'role' do usuário")

    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Decodifica e valida um token JWT."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")


# ----------------------------
# Função para obter usuário atual
# ----------------------------
def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security_scheme)
) -> dict:
    """
    Retorna um dict com id, email e role do usuário logado.
    Compatível com teleconsultas, usuários e logs.
    """
    if not credentials:
        raise HTTPException(status_code=401, detail="Token ausente")

    token = credentials.credentials
    payload = decode_token(token)

    user_id = payload.get("id")
    email = payload.get("email")
    role = payload.get("role")

    if not all([user_id, email, role]):
        raise HTTPException(status_code=401, detail="Token inválido ou usuário não encontrado")

    return {"id": user_id, "email": email, "role": role}
