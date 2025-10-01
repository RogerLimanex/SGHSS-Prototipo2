from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta

from app.models import Teleconsultation, Prescription, MedicalRecord, AuditLog, Doctor, Patient
from app.db import get_db
from app.core import security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter()
security_scheme = HTTPBearer()


# --------------------------
# Função para pegar usuário logado via token
# --------------------------
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Token ausente")
    token = credentials.credentials
    try:
        return security.decode_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido")


# --------------------------
# Função auxiliar para combinar data e hora
# --------------------------
def parse_data_hora(data: str, hora: str) -> datetime:
    try:
        dt = datetime.strptime(data, "%d/%m/%Y")
        tm = datetime.strptime(hora, "%H:%M").time()
        return datetime.combine(dt, tm)
    except ValueError:
        raise HTTPException(status_code=400, detail="Data ou hora inválida")


# --------------------------
# TELECONSULTAS CRUD
# --------------------------
@router.post("/teleconsultations", status_code=status.HTTP_201_CREATED)
def criar_teleconsulta(
        patient_id: int,
        doctor_id: int,
        data_consulta: str,
        hora_consulta: str,
        duracao_minutos: int = 30,
        observacoes: Optional[str] = None,
        db: Session = Depends(get_db),
        current=Depends(get_current_user)
):
    user_role = current.get("role")
    if user_role not in ["ADMIN", "PROFESSIONAL"]:
        raise HTTPException(status_code=403, detail="Sem permissão")

    data_hora = parse_data_hora(data_consulta, hora_consulta)
    paciente = db.query(Patient).filter(Patient.id == patient_id).first()
    medico = db.query(Doctor).filter(Doctor.id == doctor_id, Doctor.active == True).first()

    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente não encontrado")
    if not medico:
        raise HTTPException(status_code=404, detail="Médico não encontrado ou inativo")

    teleconsulta = Teleconsultation(
        patient_id=patient_id,
        doctor_id=doctor_id,
        data_hora=data_hora,
        duracao_minutos=duracao_minutos,
        observacoes=observacoes
    )
    db.add(teleconsulta)
    db.commit()
    db.refresh(teleconsulta)
    return teleconsulta


@router.get("/teleconsultations")
def listar_teleconsultas(
        patient_id: Optional[int] = None,
        doctor_id: Optional[int] = None,
        db: Session = Depends(get_db),
        current=Depends(get_current_user)
):
    query = db.query(Teleconsultation)
    if patient_id:
        query = query.filter(Teleconsultation.patient_id == patient_id)
    if doctor_id:
        query = query.filter(Teleconsultation.doctor_id == doctor_id)
    return query.all()


@router.put("/teleconsultations/{id}")
def atualizar_teleconsulta(
        id: int,
        status: Optional[str] = None,
        observacoes: Optional[str] = None,
        db: Session = Depends(get_db),
        current=Depends(get_current_user)
):
    teleconsulta = db.query(Teleconsultation).filter(Teleconsultation.id == id).first()
    if not teleconsulta:
        raise HTTPException(status_code=404, detail="Teleconsulta não encontrada")

    if status:
        teleconsulta.status = status
    if observacoes is not None:
        teleconsulta.observacoes = observacoes

    db.commit()
    db.refresh(teleconsulta)
    return teleconsulta


@router.delete("/teleconsultations/{id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_teleconsulta(id: int, db: Session = Depends(get_db), current=Depends(get_current_user)):
    teleconsulta = db.query(Teleconsultation).filter(Teleconsultation.id == id).first()
    if not teleconsulta:
        raise HTTPException(status_code=404, detail="Teleconsulta não encontrada")
    db.delete(teleconsulta)
    db.commit()
    return None


# --------------------------
# PRESCRIÇÕES CRUD
# --------------------------
@router.post("/prescriptions", status_code=status.HTTP_201_CREATED)
def criar_prescricao(
        patient_id: int,
        doctor_id: int,
        descricao: str,
        db: Session = Depends(get_db),
        current=Depends(get_current_user)
):
    user_role = current.get("role")
    if user_role not in ["ADMIN", "PROFESSIONAL"]:
        raise HTTPException(status_code=403, detail="Sem permissão")

    paciente = db.query(Patient).filter(Patient.id == patient_id).first()
    medico = db.query(Doctor).filter(Doctor.id == doctor_id).first()

    if not paciente or not medico:
        raise HTTPException(status_code=404, detail="Paciente ou médico não encontrado")

    prescricao = Prescription(
        patient_id=patient_id,
        doctor_id=doctor_id,
        descricao=descricao
    )
    db.add(prescricao)
    db.commit()
    db.refresh(prescricao)
    return prescricao


@router.get("/prescriptions")
def listar_prescricoes(
        patient_id: Optional[int] = None,
        doctor_id: Optional[int] = None,
        db: Session = Depends(get_db),
        current=Depends(get_current_user)
):
    query = db.query(Prescription)
    if patient_id:
        query = query.filter(Prescription.patient_id == patient_id)
    if doctor_id:
        query = query.filter(Prescription.doctor_id == doctor_id)
    return query.all()


@router.put("/prescriptions/{id}")
def atualizar_prescricao(
        id: int,
        descricao: Optional[str] = None,
        status: Optional[str] = None,
        db: Session = Depends(get_db),
        current=Depends(get_current_user)
):
    prescricao = db.query(Prescription).filter(Prescription.id == id).first()
    if not prescricao:
        raise HTTPException(status_code=404, detail="Prescrição não encontrada")
    if descricao is not None:
        prescricao.descricao = descricao
    if status is not None:
        prescricao.status = status
    db.commit()
    db.refresh(prescricao)
    return prescricao


@router.delete("/prescriptions/{id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_prescricao(id: int, db: Session = Depends(get_db), current=Depends(get_current_user)):
    prescricao = db.query(Prescription).filter(Prescription.id == id).first()
    if not prescricao:
        raise HTTPException(status_code=404, detail="Prescrição não encontrada")
    db.delete(prescricao)
    db.commit()
    return None


# --------------------------
# PRONTUÁRIOS CRUD
# --------------------------
@router.post("/medical_records", status_code=status.HTTP_201_CREATED)
def criar_prontuario(
        patient_id: int,
        doctor_id: int,
        descricao: str,
        db: Session = Depends(get_db),
        current=Depends(get_current_user)
):
    prontuario = MedicalRecord(
        patient_id=patient_id,
        doctor_id=doctor_id,
        descricao=descricao
    )
    db.add(prontuario)
    db.commit()
    db.refresh(prontuario)
    return prontuario


@router.get("/medical_records")
def listar_prontuarios(
        patient_id: Optional[int] = None,
        doctor_id: Optional[int] = None,
        db: Session = Depends(get_db),
        current=Depends(get_current_user)
):
    query = db.query(MedicalRecord)
    if patient_id:
        query = query.filter(MedicalRecord.patient_id == patient_id)
    if doctor_id:
        query = query.filter(MedicalRecord.doctor_id == doctor_id)
    return query.all()


# --------------------------
# LOGS CRUD
# --------------------------
@router.post("/audit_logs", status_code=status.HTTP_201_CREATED)
def criar_log(
        user_id: int,
        action: str,
        ip_address: Optional[str] = None,
        db: Session = Depends(get_db)
):
    log = AuditLog(
        user_id=user_id,
        action=action,
        ip_address=ip_address
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


@router.get("/audit_logs")
def listar_logs(db: Session = Depends(get_db)):
    return db.query(AuditLog).all()
