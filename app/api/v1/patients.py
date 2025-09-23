from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Optional
from app.db import session, models as m
from app.core import security

router = APIRouter()

def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail='Token ausente')
    token = authorization.split(' ',1)[1]
    try:
        payload = security.decode_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail='Token inválido')
    return payload

@router.get('/')
def listar_pacientes(page:int=1, size:int=20, current=Depends(get_current_user)):
    role = current.get('role')
    db = session.get_db_session()
    try:
        if role not in ['ADMIN','PROFESSIONAL']:
            raise HTTPException(status_code=403, detail='Sem permissão')
        total = db.query(m.Patient).count()
        items = db.query(m.Patient).offset((page-1)*size).limit(size).all()
        result = [{'id':p.id, 'nome': p.nome} for p in items]
        return {'items': result, 'total': total}
    finally:
        db.close()
