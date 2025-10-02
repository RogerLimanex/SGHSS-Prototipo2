from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta

from app.db import get_db
from app.models import Consulta, Paciente, Medico, StatusConsulta, LogAuditoria, PapelUsuario
from app.core.security import get_current_user

roteador = APIRouter()


# --------------------------
# Função para converter data e hora
# --------------------------
def parse_data_hora(data_consulta: str, hora_consulta: str) -> datetime:
    # tenta diferentes separadores (/, -) para aceitar formatos comuns
    for sep in ('/', '-'):
        try:
            data_formatada = datetime.strptime(data_consulta, f"%d{sep}%m{sep}%Y")
            hora_formatada = datetime.strptime(hora_consulta, "%H:%M").time()
            return datetime.combine(data_formatada, hora_formatada)
        except ValueError:
            continue
    raise HTTPException(status_code=400, detail="Data ou hora inválida")


def formatar_data_hora(dt: datetime):
    # retorna dicionário com data e hora formatadas
    return {
        "data_consulta": dt.strftime("%d/%m/%Y"),
        "hora_consulta": dt.strftime("%H:%M")
    }


# --------------------------
# LISTAR CONSULTAS
# --------------------------
@roteador.get("/")
def listar_consultas(
        page: int = 1,
        size: int = 20,
        status_filter: Optional[str] = None,
        medico_id: Optional[int] = None,
        paciente_id: Optional[int] = None,
        current=Depends(get_current_user),
        db: Session = Depends(get_db)
):
    # recupera papel e id do usuário atual a partir do token
    papel = current.get("role")
    user_id = int(current.get("sub")) if current.get("sub") else None

    query = db.query(Consulta)

    if papel == PapelUsuario.PACIENTE.value:
        query = query.filter(Consulta.paciente_id == user_id)
    elif papel == PapelUsuario.MEDICO.value:
        query = query.filter(Consulta.medico_id == user_id)

    if status_filter:
        try:
            status_enum = StatusConsulta(status_filter.lower())
            query = query.filter(Consulta.status == status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail="Status inválido")

    if medico_id:
        query = query.filter(Consulta.medico_id == medico_id)
    if paciente_id:
        query = query.filter(Consulta.paciente_id == paciente_id)

    total = query.count()
    items = query.offset((page - 1) * size).limit(size).all()

    resultado = []
    for c in items:
        resultado.append({
            "id": c.id,
            "paciente_id": c.paciente_id,
            "medico_id": c.medico_id,
            **formatar_data_hora(c.data_hora),
            "duracao_minutos": c.duracao_minutos,
            "status": c.status.value,
            "observacoes": c.observacoes
        })

    return {"items": resultado, "total": total}


# --------------------------
# OBTER CONSULTA POR ID
# --------------------------
@roteador.get("/{consulta_id}")
def obter_consulta(consulta_id: int, current=Depends(get_current_user), db: Session = Depends(get_db)):
    consulta = db.query(Consulta).filter(Consulta.id == consulta_id).first()
    if not consulta:
        raise HTTPException(status_code=404, detail="Consulta não encontrada")

    papel = current.get("role")
    user_id = int(current.get("sub")) if current.get("sub") else None

    if papel == PapelUsuario.PACIENTE.value and consulta.paciente_id != user_id:
        raise HTTPException(status_code=403, detail="Sem permissão")
    if papel == PapelUsuario.MEDICO.value and consulta.medico_id != user_id:
        raise HTTPException(status_code=403, detail="Sem permissão")

    return {
        "id": consulta.id,
        "paciente_id": consulta.paciente_id,
        "medico_id": consulta.medico_id,
        **formatar_data_hora(consulta.data_hora),
        "duracao_minutos": consulta.duracao_minutos,
        "status": consulta.status.value,
        "observacoes": consulta.observacoes
    }


# --------------------------
# CRIAR CONSULTA
# --------------------------
@roteador.post("/", status_code=status.HTTP_201_CREATED)
def criar_consulta(
        paciente_id: int,
        medico_id: int,
        data_consulta: str,
        hora_consulta: str,
        duracao_minutos: int = 30,
        observacoes: Optional[str] = None,
        current=Depends(get_current_user),
        db: Session = Depends(get_db)
):
    # somente ADMIN e MEDICO podem criar consultas
    if current.get("role") not in [PapelUsuario.ADMIN.value, PapelUsuario.MEDICO.value]:
        raise HTTPException(status_code=403, detail="Sem permissão para agendar consultas")

    data_hora = parse_data_hora(data_consulta, hora_consulta)

    paciente = db.query(Paciente).filter(Paciente.id == paciente_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente não encontrado")

    medico = db.query(Medico).filter(Medico.id == medico_id, Medico.ativo == True).first()
    if not medico:
        raise HTTPException(status_code=404, detail="Médico não encontrado ou inativo")

    fim = data_hora + timedelta(minutes=duracao_minutos)
    conflito = db.query(Consulta).filter(
        Consulta.medico_id == medico_id,
        Consulta.data_hora < fim,
        (Consulta.data_hora + timedelta(minutes=Consulta.duracao_minutos)) > data_hora,
        Consulta.status != StatusConsulta.CANCELADA
    ).first()
    if conflito:
        raise HTTPException(status_code=400, detail="Médico já possui consulta neste horário")

    consulta = Consulta(
        paciente_id=paciente_id,
        medico_id=medico_id,
        data_hora=data_hora,
        duracao_minutos=duracao_minutos,
        observacoes=observacoes,
        status=StatusConsulta.AGENDADA
    )

    db.add(consulta)
    db.commit()
    db.refresh(consulta)

    # Auditoria
    log = LogAuditoria(usuario_id=current.get("sub"), acao="Criou consulta")
    db.add(log)
    db.commit()

    return {
        "id": consulta.id,
        "paciente_id": consulta.paciente_id,
        "medico_id": consulta.medico_id,
        **formatar_data_hora(consulta.data_hora),
        "duracao_minutos": consulta.duracao_minutos,
        "status": consulta.status.value,
        "observacoes": consulta.observacoes
    }


# --------------------------
# ATUALIZAR CONSULTA
# --------------------------
@roteador.put("/{consulta_id}")
def atualizar_consulta(
        consulta_id: int,
        data_consulta: Optional[str] = None,
        hora_consulta: Optional[str] = None,
        status_update: Optional[str] = None,
        observacoes: Optional[str] = None,
        current=Depends(get_current_user),
        db: Session = Depends(get_db)
):
    consulta = db.query(Consulta).filter(Consulta.id == consulta_id).first()
    if not consulta:
        raise HTTPException(status_code=404, detail="Consulta não encontrada")

    papel = current.get("role")
    user_id = int(current.get("sub")) if current.get("sub") else None

    if papel == PapelUsuario.PACIENTE.value:
        raise HTTPException(status_code=403, detail="Pacientes não podem alterar consultas")

    if papel == PapelUsuario.MEDICO.value and consulta.medico_id != user_id:
        raise HTTPException(status_code=403, detail="Sem permissão")

    if status_update:
        try:
            consulta.status = StatusConsulta(status_update.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail="Status inválido")

    if data_consulta and hora_consulta:
        consulta.data_hora = parse_data_hora(data_consulta, hora_consulta)

    if observacoes is not None:
        consulta.observacoes = observacoes

    db.commit()
    db.refresh(consulta)

    # Auditoria
    log = LogAuditoria(usuario_id=current.get("sub"), acao="Atualizou consulta")
    db.add(log)
    db.commit()

    return {
        "id": consulta.id,
        "paciente_id": consulta.paciente_id,
        "medico_id": consulta.medico_id,
        **formatar_data_hora(consulta.data_hora),
        "duracao_minutos": consulta.duracao_minutos,
        "status": consulta.status.value,
        "observacoes": consulta.observacoes
    }


# --------------------------
# CANCELAR CONSULTA
# --------------------------
@roteador.delete("/{consulta_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancelar_consulta(consulta_id: int, current=Depends(get_current_user), db: Session = Depends(get_db)):
    consulta = db.query(Consulta).filter(Consulta.id == consulta_id).first()
    if not consulta:
        raise HTTPException(status_code=404, detail="Consulta não encontrada")

    papel = current.get("role")
    user_id = int(current.get("sub")) if current.get("sub") else None

    if papel == PapelUsuario.PACIENTE.value and consulta.paciente_id != user_id:
        raise HTTPException(status_code=403, detail="Sem permissão")
    if papel == PapelUsuario.MEDICO.value and consulta.medico_id != user_id:
        raise HTTPException(status_code=403, detail="Sem permissão")

    consulta.status = StatusConsulta.CANCELADA
    db.commit()

    # Auditoria
    log = LogAuditoria(usuario_id=current.get("sub"), acao="Cancelou consulta")
    db.add(log)
    db.commit()
    return None
