from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session  # ← Adicione
from app.db import get_db_session  # ← Use a função correta
from app import models as m  # ← Import correto
from app.core import security

router = APIRouter()


class LoginIn(BaseModel):
    email: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = 'bearer'


@router.post('/login', response_model=TokenOut)
def login(payload: LoginIn, db: Session = Depends(get_db_session)):  # ← Corrigido
    try:
        user = db.query(m.User).filter(m.User.email == payload.email).first()
        if not user or not security.verify_password(payload.password, user.hashed_password):
            raise HTTPException(status_code=401, detail='Credenciais inválidas')
        token = security.create_access_token({'sub': str(user.id), 'role': user.role})
        return {'access_token': token}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@router.post('/_create_test_admin', status_code=201)
def create_test_admin(db: Session = Depends(get_db_session)):  # ← Corrigido
    if db.query(m.User).filter(m.User.email == 'admin@vidaplus.com').first():
        raise HTTPException(status_code=400, detail='Já existe')

    user = m.User(
        email='admin@vidaplus.com',
        hashed_password=security.hash_password('adminpass'),
        role='ADMIN'
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {'id': user.id, 'email': user.email}
