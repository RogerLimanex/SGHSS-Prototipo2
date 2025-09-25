from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db import get_db_session
from app import models as m
from app.core import security

router = APIRouter()
security_scheme = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)):
    if not credentials:
        raise HTTPException(status_code=401, detail='Token ausente')
    token = credentials.credentials
    try:
        return security.decode_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail='Token inválido')


# GET ALL - Já existe
@router.get('/')
def listar_pacientes(
        page: int = 1,
        size: int = 20,
        current=Depends(get_current_user),
        db: Session = Depends(get_db_session)
):
    if current.get('role') not in ['ADMIN', 'PROFESSIONAL']:
        raise HTTPException(status_code=403, detail='Sem permissão')

    total = db.query(m.Patient).count()
    items = db.query(m.Patient).offset((page - 1) * size).limit(size).all()
    return {'items': items, 'total': total}


# GET BY ID
@router.get('/{patient_id}')
def obter_paciente(
        patient_id: int,
        current=Depends(get_current_user),
        db: Session = Depends(get_db_session)
):
    if current.get('role') not in ['ADMIN', 'PROFESSIONAL']:
        raise HTTPException(status_code=403, detail='Sem permissão')

    patient = db.query(m.Patient).filter(m.Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail='Paciente não encontrado')
    return patient


# CREATE
@router.post('/', status_code=status.HTTP_201_CREATED)
def criar_paciente(
        nome: str,
        email: str,
        telefone: Optional[str] = None,
        cpf: Optional[str] = None,
        data_nascimento: Optional[str] = None,
        endereco: Optional[str] = None,
        current=Depends(get_current_user),
        db: Session = Depends(get_db_session)
):
    if current.get('role') not in ['ADMIN', 'PROFESSIONAL']:
        raise HTTPException(status_code=403, detail='Sem permissão')

    # Verificar se email já existe
    if db.query(m.Patient).filter(m.Patient.email == email).first():
        raise HTTPException(status_code=400, detail='Email já cadastrado')

    patient = m.Patient(
        nome=nome,
        email=email,
        telefone=telefone,
        cpf=cpf,
        endereco=endereco
    )

    # Converter data - aceitar múltiplos formatos
    if data_nascimento:
        from datetime import datetime

        # Tentar diferentes formatos
        formats = ['%Y-%m-%d', '%d%m%Y', '%d-%m-%Y', '%d-%m-%y', '%d/%m/%Y', '%d/%m/%y']

        for fmt in formats:
            try:
                patient.data_nascimento = datetime.strptime(data_nascimento, fmt).date()
                break  # Se funcionar, sai do loop
            except ValueError:
                continue  # Tenta próximo formato
        else:
            # Se nenhum formato funcionou
            raise HTTPException(
                status_code=400,
                detail=f'Formato de data inválido: {data_nascimento}. Use AAAA-MM-DD'
            )

    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


# UPDATE
@router.put('/{patient_id}')
def atualizar_paciente(
        patient_id: int,
        nome: Optional[str] = None,
        email: Optional[str] = None,
        telefone: Optional[str] = None,
        endereco: Optional[str] = None,
        current=Depends(get_current_user),
        db: Session = Depends(get_db_session)
):
    if current.get('role') not in ['ADMIN', 'PROFESSIONAL']:
        raise HTTPException(status_code=403, detail='Sem permissão')

    patient = db.query(m.Patient).filter(m.Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail='Paciente não encontrado')

    # Atualizar campos fornecidos
    if nome is not None:
        patient.nome = nome
    if email is not None:
        patient.email = email
    if telefone is not None:
        patient.telefone = telefone
    if endereco is not None:
        patient.endereco = endereco

    db.commit()
    db.refresh(patient)
    return patient


# DELETE
@router.delete('/{patient_id}', status_code=status.HTTP_204_NO_CONTENT)
def deletar_paciente(
        patient_id: int,
        current=Depends(get_current_user),
        db: Session = Depends(get_db_session)
):
    if current.get('role') != 'ADMIN':
        raise HTTPException(status_code=403, detail='Apenas administradores podem excluir')

    patient = db.query(m.Patient).filter(m.Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail='Paciente não encontrado')

    db.delete(patient)
    db.commit()
    return None
