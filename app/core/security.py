import os
from datetime import datetime, timedelta
import bcrypt  # usamos apenas bcrypt agora
from jose import jwt, JWTError
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# ----------------------------
# Configurações de segurança
# ----------------------------
JWT_SECRET = os.getenv('JWT_SECRET', 'CHANGE_ME')
JWT_ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 60

security_scheme = HTTPBearer()


# ----------------------------
# Funções de senha e token usando bcrypt puro
# ----------------------------
def hash_password(password: str) -> str:
    # gera salt e hash da senha
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({'exp': expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")


# ----------------------------
# Função para obter usuário atual
# ----------------------------
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Token ausente")
    token = credentials.credentials
    return decode_token(token)
