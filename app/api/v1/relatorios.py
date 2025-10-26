from fastapi import APIRouter, Depends, HTTPException  # FastAPI imports
from sqlalchemy.orm import Session  # Sessão do SQLAlchemy
from datetime import datetime, date  # Para manipulação de datas
from app.db import get_db  # Sessão do banco
from app import models as m  # Models do projeto
from app.core import security  # Segurança e autenticação
from app.utils.logs import registrar_log  # Função utilitária para logs

roteador = APIRouter()  # Cria o roteador FastAPI


# ----------------------------
# Obter usuário atual garantindo email
# ----------------------------
def obter_usuario_atual(current_user=Depends(security.get_current_user), db: Session = Depends(get_db)):
    """
    Garante que o usuário autenticado tenha o campo 'email' disponível.
    Evita falhas nos logs quando o token JWT não contém o email.
    """
    usuario_email = current_user.get("email")
    if not usuario_email:  # Se não houver email no token
        usuario = db.query(m.Usuario).filter(m.Usuario.id == int(current_user.get("id"))).first()
        if usuario:
            usuario_email = usuario.email
            current_user["email"] = usuario.email
    return current_user  # Retorna usuário com email garantido


# ----------------------------
# Função auxiliar para converter DD/MM/YYYY em datetime.date
# ----------------------------
def parse_data_br(data_str: str) -> date:
    """
    Converte uma string no formato DD/MM/YYYY para um objeto datetime.date.
    Lança HTTPException 400 caso a string não esteja no formato esperado.
    """
    try:
        return datetime.strptime(data_str, "%d/%m/%Y").date()
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Data inválida: {data_str}. Formato esperado DD/MM/YYYY")


# ----------------------------
# Relatório de consultas por médico
# ----------------------------
@roteador.get("/relatorios/consultas")
def relatorio_consultas(
        data_inicial: str,  # Data inicial como string
        data_final: str,  # Data final como string
        db: Session = Depends(get_db),
        usuario_atual=Depends(obter_usuario_atual)
):
    """
    Gera relatório de consultas entre duas datas.
    Permissão restrita a usuários ADMIN.
    Retorna informações do médico, data/hora, duração, status e observações.
    """
    if usuario_atual["papel"] != "ADMIN":  # Verifica permissão
        raise HTTPException(status_code=403, detail="Acesso negado: apenas ADMIN")

    data_ini = parse_data_br(data_inicial)  # Converte data inicial
    data_fim = parse_data_br(data_final)  # Converte data final

    consultas = db.query(m.Consulta).join(m.Medico).filter(
        m.Consulta.data_hora.between(data_ini, data_fim)
    ).all()  # Busca consultas entre datas

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
                  detalhes=f"Relatório de consultas de {data_inicial} a {data_final}")  # Log

    return {"data_inicial": data_inicial, "data_final": data_final, "items": retorno}  # Retorno


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
    """
    Gera relatório de prontuários entre duas datas.
    Permissão restrita a usuários ADMIN.
    Inclui informações do paciente, médico, descrição, status, data/hora e anexo.
    """
    if usuario_atual["papel"] != "ADMIN":
        raise HTTPException(status_code=403, detail="Acesso negado: apenas ADMIN")

    data_ini = parse_data_br(data_inicial)
    data_fim = parse_data_br(data_final)

    prontuarios = db.query(m.Prontuario).join(m.Paciente).join(m.Medico, isouter=True).filter(
        m.Prontuario.data_hora.between(data_ini, data_fim)
    ).all()  # Busca prontuários entre datas

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
    """
    Gera relatório de teleconsultas entre duas datas.
    Permissão restrita a usuários ADMIN ou MEDICO.
    Retorna informações do paciente, médico, data/hora, duração, status e link de vídeo.
    """
    if usuario_atual["papel"] not in ["ADMIN", "MEDICO"]:
        raise HTTPException(status_code=403, detail="Acesso negado")

    data_ini = parse_data_br(data_inicial)
    data_fim = parse_data_br(data_final)

    registros = db.query(m.Teleconsulta).join(m.Consulta).join(m.Paciente).join(m.Medico).filter(
        m.Teleconsulta.data_hora.between(data_ini, data_fim)
    ).all()  # Busca teleconsultas

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
    """
    Gera relatório geral resumido do sistema.
    Permissão restrita a usuários ADMIN.
    Inclui totais de pacientes, médicos, prontuários, consultas e teleconsultas.
    """
    if usuario_atual["papel"] != "ADMIN":
        raise HTTPException(status_code=403, detail="Acesso negado")

    total_pacientes = db.query(m.Paciente).count()
    total_medicos = db.query(m.Medico).count()
    total_prontuarios = db.query(m.Prontuario).count()
    total_consultas = db.query(m.Consulta).count()
    total_teleconsultas = db.query(m.Teleconsulta).count()  # Conta registros

    registrar_log(db, usuario_atual["email"], "Relatorio", acao="READ",
                  detalhes="Relatório geral gerado")  # Log

    return {
        "total_pacientes": total_pacientes,
        "total_medicos": total_medicos,
        "total_prontuarios": total_prontuarios,
        "total_consultas": total_consultas,
        "total_teleconsultas": total_teleconsultas
    }
