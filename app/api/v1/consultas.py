from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import Optional
from datetime import datetime, timedelta

from app.db import get_db
from app.models.medical import Consulta, Paciente, Medico, StatusConsulta, PapelUsuario, Usuario
from app.core import security
from app.utils.logs import registrar_log

roteador = APIRouter()


# --------------------------
# Função para converter data e hora
# --------------------------
def parse_data_hora(data: str, hora: str) -> datetime:
    for sep in ('/', '-'):
        try:
            data_formatada = datetime.strptime(data, f"%d{sep}%m{sep}%Y")
            hora_formatada = datetime.strptime(hora, "%H:%M").time()
            return datetime.combine(data_formatada, hora_formatada)
        except ValueError:
            continue
    raise HTTPException(status_code=400, detail="Data ou hora inválida")


def formatar_data_hora(dt: datetime) -> dict:
    return {
        "data_consulta": dt.strftime("%d/%m/%Y"),
        "hora_consulta": dt.strftime("%H:%M")
    }


# --------------------------
# Obter usuário atual com email garantido
# --------------------------
def obter_usuario_atual(
        current_user=Depends(security.get_current_user),
        db: Session = Depends(get_db)
):
    usuario_email = current_user.get("email")
    if not usuario_email:
        usuario = db.query(Usuario).filter(Usuario.id == int(current_user.get("sub"))).first()
        if usuario:
            usuario_email = usuario.email
            current_user["email"] = usuario.email
    return current_user


# --------------------------
# LISTAR CONSULTAS
# --------------------------
@roteador.get("/")
def listar_consultas(
        pagina: int = 1,
        tamanho: int = 20,
        status_filtro: Optional[str] = None,
        medico_id: Optional[int] = None,
        paciente_id: Optional[int] = None,
        usuario_atual=Depends(obter_usuario_atual),
        db: Session = Depends(get_db)
):
    papel = usuario_atual.get("role")
    user_id = int(usuario_atual.get("sub")) if usuario_atual.get("sub") else None

    query = db.query(Consulta)

    if papel == PapelUsuario.PACIENTE.value:
        query = query.filter(Consulta.paciente_id == user_id)
    elif papel == PapelUsuario.MEDICO.value:
        query = query.filter(Consulta.medico_id == user_id)

    if status_filtro:
        try:
            status_enum = StatusConsulta(status_filtro.lower())
            query = query.filter(Consulta.status == status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail="Status inválido")

    if medico_id:
        query = query.filter(Consulta.medico_id == medico_id)
    if paciente_id:
        query = query.filter(Consulta.paciente_id == paciente_id)

    total = query.count()
    itens = query.offset((pagina - 1) * tamanho).limit(tamanho).all()

    registrar_log(
        db=db,
        usuario_email=usuario_atual.get("email"),
        tabela="consultas",
        acao="READ",
        detalhes=f"{usuario_atual.get('email')} listou consultas (página {pagina})"
    )

    resultado = []
    for c in itens:
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
def obter_consulta(
        consulta_id: int,
        usuario_atual=Depends(obter_usuario_atual),
        db: Session = Depends(get_db)
):
    consulta = db.query(Consulta).filter(Consulta.id == consulta_id).first()
    if not consulta:
        raise HTTPException(status_code=404, detail="Consulta não encontrada")

    papel = usuario_atual.get("role")
    user_id = int(usuario_atual.get("sub")) if usuario_atual.get("sub") else None

    if papel == PapelUsuario.PACIENTE.value and consulta.paciente_id != user_id:
        raise HTTPException(status_code=403, detail="Sem permissão")
    if papel == PapelUsuario.MEDICO.value and consulta.medico_id != user_id:
        raise HTTPException(status_code=403, detail="Sem permissão")

    registrar_log(
        db=db,
        usuario_email=usuario_atual.get("email"),
        tabela="consultas",
        registro_id=consulta.id,
        acao="READ",
        detalhes=f"{usuario_atual.get('email')} acessou consulta ID {consulta.id}"
    )

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
        usuario_atual=Depends(obter_usuario_atual),
        db: Session = Depends(get_db)
):
    if usuario_atual.get("role") not in [PapelUsuario.ADMIN.value, PapelUsuario.MEDICO.value]:
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
        Consulta.status != StatusConsulta.CANCELADA,
        and_(
            Consulta.data_hora < fim,
            func.datetime(Consulta.data_hora, f'+{Consulta.duracao_minutos} minutes') > data_hora
        )
    ).first()

    if conflito:
        raise HTTPException(status_code=400, detail="Médico já possui consulta neste horário")

    nova_consulta = Consulta(
        paciente_id=paciente_id,
        medico_id=medico_id,
        data_hora=data_hora,
        duracao_minutos=duracao_minutos,
        observacoes=observacoes,
        status=StatusConsulta.AGENDADA
    )

    db.add(nova_consulta)
    db.commit()
    db.refresh(nova_consulta)

    registrar_log(
        db=db,
        usuario_email=usuario_atual.get("email"),
        tabela="consultas",
        registro_id=nova_consulta.id,
        acao="CREATE",
        detalhes=f"Consulta criada por {usuario_atual.get('email')} para paciente {paciente_id} e médico {medico_id}"
    )

    return {
        "id": nova_consulta.id,
        "paciente_id": nova_consulta.paciente_id,
        "medico_id": nova_consulta.medico_id,
        **formatar_data_hora(nova_consulta.data_hora),
        "duracao_minutos": nova_consulta.duracao_minutos,
        "status": nova_consulta.status.value,
        "observacoes": nova_consulta.observacoes
    }


# --------------------------
# ATUALIZAR CONSULTA
# --------------------------
@roteador.patch("/{consulta_id}")
def atualizar_consulta(
        consulta_id: int,
        data_consulta: Optional[str] = None,
        hora_consulta: Optional[str] = None,
        status_update: Optional[str] = None,
        observacoes: Optional[str] = None,
        usuario_atual=Depends(obter_usuario_atual),
        db: Session = Depends(get_db)
):
    consulta = db.query(Consulta).filter(Consulta.id == consulta_id).first()
    if not consulta:
        raise HTTPException(status_code=404, detail="Consulta não encontrada")

    papel = usuario_atual.get("role")
    user_id = int(usuario_atual.get("sub")) if usuario_atual.get("sub") else None

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

    registrar_log(
        db=db,
        usuario_email=usuario_atual.get("email"),
        tabela="consultas",
        registro_id=consulta.id,
        acao="UPDATE",
        detalhes=f"Consulta {consulta_id} atualizada por {usuario_atual.get('email')}"
    )

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
@roteador.patch("/{consulta_id}/cancelar", response_model=dict)
def cancelar_consulta(
        consulta_id: int,
        usuario_atual=Depends(obter_usuario_atual),
        db: Session = Depends(get_db)
):
    consulta = db.query(Consulta).filter(Consulta.id == consulta_id).first()
    if not consulta:
        raise HTTPException(status_code=404, detail="Consulta não encontrada")

    papel = usuario_atual.get("role")
    user_id = int(usuario_atual.get("sub")) if usuario_atual.get("sub") else None

    if papel == PapelUsuario.PACIENTE.value and consulta.paciente_id != user_id:
        raise HTTPException(status_code=403, detail="Sem permissão")
    if papel == PapelUsuario.MEDICO.value and consulta.medico_id != user_id:
        raise HTTPException(status_code=403, detail="Sem permissão")

    consulta.status = StatusConsulta.CANCELADA
    db.commit()
    db.refresh(consulta)

    registrar_log(
        db=db,
        usuario_email=usuario_atual.get("email"),
        tabela="consultas",
        registro_id=consulta.id,
        acao="DELETE",
        detalhes=f"Consulta {consulta_id} cancelada por {usuario_atual.get('email')}"
    )

    return {"id": consulta.id, "status": consulta.status.value}
