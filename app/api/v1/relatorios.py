# D:\ProjectSGHSS\app\api\v1\relatorios.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date
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
# Relatório de consultas por médico
# ----------------------------
@roteador.get("/relatorios/consultas")
def relatorio_consultas(
        data_inicial: date,
        data_final: date,
        db: Session = Depends(get_db),
        usuario_atual=Depends(obter_usuario_atual)
):
    if usuario_atual["papel"] != "ADMIN":
        raise HTTPException(status_code=403, detail="Acesso negado: apenas ADMIN")

    resultados = db.query(
        m.Consulta.medico_id,
        m.Medico.nome,
    ).filter(m.Consulta.data_agendamento.between(data_inicial, data_final)).all()

    registrar_log(db, usuario_atual["email"], "Relatorio", acao="READ",
                  detalhes=f"Relatório de consultas de {data_inicial} a {data_final}")

    return resultados


# ----------------------------
# Relatório de prontuários
# ----------------------------
@roteador.get("/relatorios/prontuarios")
def relatorio_prontuarios(
        data_inicial: date,
        data_final: date,
        db: Session = Depends(get_db),
        usuario_atual=Depends(obter_usuario_atual)
):
    if usuario_atual["papel"] != "ADMIN":
        raise HTTPException(status_code=403, detail="Acesso negado")

    total = db.query(m.Prontuario).filter(m.Prontuario.data_hora.between(data_inicial, data_final)).count()

    registrar_log(db, usuario_atual["email"], "Relatorio", acao="READ",
                  detalhes="Relatório de prontuários gerado")

    return {"total_prontuarios": total}


# ----------------------------
# Relatório de telemedicina
# ----------------------------
@roteador.get("/relatorios/telemedicina")
def relatorio_telemedicina(
        db: Session = Depends(get_db),
        usuario_atual=Depends(obter_usuario_atual)
):
    if usuario_atual["papel"] not in ["ADMIN", "MEDICO"]:
        raise HTTPException(status_code=403, detail="Acesso negado")

    registros = db.query(m.Prontuario).filter(m.Prontuario.anexo.like("%.teleconsulta%")).all()

    registrar_log(db, usuario_atual["email"], "Relatorio", acao="READ",
                  detalhes="Relatório de telemedicina gerado")

    return {"total_teleconsultas": len(registros)}


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

    registrar_log(db, usuario_atual["email"], "Relatorio", acao="READ",
                  detalhes="Relatório geral gerado")

    return {
        "pacientes": total_pacientes,
        "medicos": total_medicos,
        "prontuarios": total_prontuarios
    }
