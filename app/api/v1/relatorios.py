# D:\ProjectSGHSS\app\api\v1\relatorios.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, date
from app.db import get_db
from app import models as m
from app.core import security
from app.utils.logs import registrar_log

roteador = APIRouter()


def obter_usuario_atual(current_user=Depends(security.get_current_user), db: Session = Depends(get_db)):
    usuario_email = current_user.get("email")
    if not usuario_email:
        usuario = db.query(m.Usuario).filter(m.Usuario.id == int(current_user.get("id"))).first()
        if usuario:
            usuario_email = usuario.email
            current_user["email"] = usuario.email
    return current_user


# ----------------------------
# Função auxiliar para converter DD/MM/YYYY em datetime.date
# ----------------------------
def parse_data_br(data_str: str) -> date:
    try:
        return datetime.strptime(data_str, "%d/%m/%Y").date()
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Data inválida: {data_str}. Formato esperado DD/MM/YYYY")


# ----------------------------
# Relatório de consultas por médico
# ----------------------------
@roteador.get("/relatorios/consultas")
def relatorio_consultas(
        data_inicial: str,
        data_final: str,
        db: Session = Depends(get_db),
        usuario_atual=Depends(obter_usuario_atual)
):
    if usuario_atual["papel"] != "ADMIN":
        raise HTTPException(status_code=403, detail="Acesso negado: apenas ADMIN")

    data_ini = parse_data_br(data_inicial)
    data_fim = parse_data_br(data_final)

    consultas = db.query(m.Consulta).join(m.Medico).filter(
        m.Consulta.data_hora.between(data_ini, data_fim)
    ).all()

    retorno = []
    for c in consultas:
        data_consulta = c.data_hora.strftime("%d/%m/%Y") if c.data_hora else None
        hora_consulta = c.data_hora.strftime("%H:%M") if c.data_hora else None
        retorno.append({
            "medico_id": c.medico.id,
            "medico_nome": c.medico.nome,
            "data_consulta": data_consulta,
            "hora_consulta": hora_consulta,
            "duracao_minutos": c.duracao_minutos,
            "status": c.status.value,
            "observacoes": c.observacoes
        })

    registrar_log(db, usuario_atual["email"], "Relatorio", acao="READ",
                  detalhes=f"Relatório de consultas de {data_inicial} a {data_final}")

    return {"data_inicial": data_inicial, "data_final": data_final, "items": retorno}


# ----------------------------
# Relatório de prontuários
# ----------------------------
@roteador.get("/relatorios/prontuarios")
def relatorio_prontuarios(
        data_inicial: str,
        data_final: str,
        db: Session = Depends(get_db),
        usuario_atual=Depends(obter_usuario_atual)
):
    if usuario_atual["papel"] != "ADMIN":
        raise HTTPException(status_code=403, detail="Acesso negado: apenas ADMIN")

    data_ini = parse_data_br(data_inicial)
    data_fim = parse_data_br(data_final)

    prontuarios = db.query(m.Prontuario).join(m.Paciente).join(m.Medico, isouter=True).filter(
        m.Prontuario.data_hora.between(data_ini, data_fim)
    ).all()

    retorno = []
    for p in prontuarios:
        data_hora = p.data_hora.strftime("%d/%m/%Y %H:%M") if p.data_hora else None
        retorno.append({
            "prontuario_id": p.id,
            "paciente_nome": p.paciente.nome,
            "medico_nome": p.medico.nome if p.medico else None,
            "descricao": p.descricao,
            "status": p.status,
            "data_hora": data_hora,
            "anexo": p.anexo
        })

    registrar_log(db, usuario_atual["email"], "Relatorio", acao="READ",
                  detalhes=f"Relatório de prontuários de {data_inicial} a {data_final}")

    return {"data_inicial": data_inicial, "data_final": data_final, "items": retorno}


# ----------------------------
# Relatório de teleconsultas
# ----------------------------
@roteador.get("/relatorios/teleconsultas")
def relatorio_teleconsultas(
        data_inicial: str,
        data_final: str,
        db: Session = Depends(get_db),
        usuario_atual=Depends(obter_usuario_atual)
):
    if usuario_atual["papel"] not in ["ADMIN", "MEDICO"]:
        raise HTTPException(status_code=403, detail="Acesso negado")

    data_ini = parse_data_br(data_inicial)
    data_fim = parse_data_br(data_final)

    registros = db.query(m.Teleconsulta).join(m.Consulta).join(m.Paciente).join(m.Medico).filter(
        m.Teleconsulta.data_hora.between(data_ini, data_fim)
    ).all()

    retorno = []
    for t in registros:
        data_consulta = t.data_hora.strftime("%d/%m/%Y") if t.data_hora else None
        hora_consulta = t.data_hora.strftime("%H:%M") if t.data_hora else None
        retorno.append({
            "teleconsulta_id": t.id,
            "paciente_nome": t.consulta.paciente.nome,
            "medico_nome": t.consulta.medico.nome,
            "data_consulta": data_consulta,
            "hora_consulta": hora_consulta,
            "duracao_minutos": t.consulta.duracao_minutos,
            "status": t.status.value,
            "link_video": t.link_video
        })

    registrar_log(db, usuario_atual["email"], "Relatorio", acao="READ",
                  detalhes=f"Relatório de teleconsultas de {data_inicial} a {data_final}")

    return {"data_inicial": data_inicial, "data_final": data_final, "items": retorno}


# ----------------------------
# Relatório geral resumido
# ----------------------------
@roteador.get("/relatorios/geral")
def relatorio_geral(
        db: Session = Depends(get_db),
        usuario_atual=Depends(obter_usuario_atual)
):
    if usuario_atual["papel"] != "ADMIN":
        raise HTTPException(status_code=403, detail="Acesso negado")

    total_pacientes = db.query(m.Paciente).count()
    total_medicos = db.query(m.Medico).count()
    total_prontuarios = db.query(m.Prontuario).count()
    total_consultas = db.query(m.Consulta).count()
    total_teleconsultas = db.query(m.Teleconsulta).count()

    registrar_log(db, usuario_atual["email"], "Relatorio", acao="READ",
                  detalhes="Relatório geral gerado")

    return {
        "total_pacientes": total_pacientes,
        "total_medicos": total_medicos,
        "total_prontuarios": total_prontuarios,
        "total_consultas": total_consultas,
        "total_teleconsultas": total_teleconsultas
    }
