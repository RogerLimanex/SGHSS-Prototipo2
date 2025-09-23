from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from app.db import session, models as m
from app.core import security

router = APIRouter()

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class TokenOut(BaseModel):
    access_token: str
    token_type: str = 'bearer'

@router.post('/login', response_model=TokenOut)
def login(payload: LoginIn):
    db = session.get_db_session()
    try:
        user = db.query(m.User).filter(m.User.email==payload.email).first()
        if not user or not security.verify_password(payload.password, user.hashed_password):
            raise HTTPException(status_code=401, detail='Credenciais inválidas')
        token = security.create_access_token({'sub': str(user.id), 'role': user.role})
        return {'access_token': token}
    finally:
        db.close()

@router.post('/_create_test_admin', status_code=201)
def create_test_admin():
    db = session.get_db_session()
    if db.query(m.User).filter(m.User.email=='admin@vidaplus.test').first():
        raise HTTPException(status_code=400, detail='Já existe')
    user = m.User(email='admin@vidaplus.test', hashed_password=security.hash_password('adminpass'), role='ADMIN')
    db.add(user); db.commit(); db.refresh(user)
    db.close()
    return {'id': user.id, 'email': user.email}
