from fastapi import APIRouter, Depends, HTTPException, status, Form  # Importações FastAPI
from sqlalchemy.orm import Session  # Sessão do SQLAlchemy
from typing import List  # Tipagem para listas
from datetime import datetime  # Para registro de data/hora
from app.db import get_db  # Função para obter sessão do banco
from app import models as m  # Import dos models
from app.core import security  # Autenticação e segurança
from app.schemas import PrescricaoResponse  # Schema de resposta para prescrição
from app.utils.logs import registrar_log  # Função utilitária para registrar logs

roteador = APIRouter()  # Cria roteador FastAPI


# ============================================================
# FUNÇÃO AUXILIAR: Obter usuário atual
# ============================================================
def obter_usuario_atual(
        current_user=Depends(security.get_current_user),  # Usuário obtido via token JWT
        db: Session = Depends(get_db)  # Sessão do banco
):
    """
    Garante que o usuário autenticado tenha o campo 'email' disponível.
    Evita falhas nos logs quando o token JWT não contém o email.
    """
    usuario_email = current_user.get("email")  # Tenta obter email do token
    if not usuario_email:  # Se não existir, busca no banco
        usuario = db.query(m.Usuario).filter(m.Usuario.id == int(current_user.get("id"))).first()
        if usuario:
            usuario_email = usuario.email
            current_user["email"] = usuario.email
    return current_user  # Retorna usuário com email


# ============================================================
# 1️⃣ ENDPOINT: Criar prescrição
# ============================================================
@roteador.post("/prescricoes", response_model=PrescricaoResponse, status_code=status.HTTP_201_CREATED,
               tags=["Prescrições"])
def criar_prescricao(
        paciente_id: int = Form(...),  # ID do paciente
        medico_id: int = Form(...),  # ID do médico
        medicamento: str = Form(...),  # Nome do medicamento
        dosagem: str = Form(...),  # Dosagem indicada
        instrucoes: str = Form(...),  # Instruções de uso
        db: Session = Depends(get_db),
        usuario_atual=Depends(obter_usuario_atual)
):
    """
    Cria uma nova prescrição médica para um paciente.
    - **Acesso:** apenas MEDICO ou ADMIN
    - **Registra log** da criação
    """
    if usuario_atual.get("papel") not in ["MEDICO", "ADMIN"]:  # Valida permissão
        raise HTTPException(status_code=403, detail="Sem permissão")

    nova_prescricao = m.Receita(
        paciente_id=paciente_id,
        medico_id=medico_id,
        medicamento=medicamento,
        dosagem=dosagem,
        instrucoes=instrucoes,
        data_hora=datetime.now()  # Timestamp da criação
    )
    db.add(nova_prescricao)  # Adiciona à sessão
    db.commit()  # Salva alterações
    db.refresh(nova_prescricao)  # Atualiza objeto com ID gerado

    registrar_log(
        db=db,
        usuario_email=usuario_atual.get("email"),
        tabela="Receita",
        registro_id=nova_prescricao.id,
        acao="CREATE",
        detalhes=f"Prescrição criada para paciente {paciente_id} pelo médico {medico_id}"
    )

    return nova_prescricao  # Retorna prescrição criada


# ============================================================
# 2️⃣ ENDPOINT: Listar prescrições
# ============================================================
@roteador.get("/prescricoes", response_model=List[PrescricaoResponse], tags=["Prescrições"])
def listar_prescricoes(
        db: Session = Depends(get_db),
        usuario_atual=Depends(obter_usuario_atual)
):
    """
    Lista todas as prescrições médicas cadastradas.
    - **Acesso:** apenas MEDICO ou ADMIN
    - **Registra log** da operação
    """
    if usuario_atual.get("papel") not in ["MEDICO", "ADMIN"]:  # Valida permissão
        raise HTTPException(status_code=403, detail="Sem permissão")

    prescricoes = db.query(m.Receita).all()  # Consulta todas prescrições

    registrar_log(
        db=db,
        usuario_email=usuario_atual.get("email"),
        tabela="Receita",
        acao="READ",
        detalhes=f"{usuario_atual.get('email')} listou todas as prescrições"
    )

    return prescricoes  # Retorna lista de prescrições


# ============================================================
# 3️⃣ ENDPOINT: Cancelar prescrição
# ============================================================
@roteador.patch("/prescricoes/{prescricao_id}/cancelar", response_model=PrescricaoResponse, tags=["Prescrições"])
def cancelar_prescricao(
        prescricao_id: int,  # ID da prescrição
        db: Session = Depends(get_db),
        usuario_atual=Depends(obter_usuario_atual)
):
    """
    Cancela uma prescrição médica existente.
    - **Acesso:** apenas MEDICO ou ADMIN
    - **Registra log** do cancelamento
    """
    if usuario_atual.get("papel") not in ["MEDICO", "ADMIN"]:  # Valida permissão
        raise HTTPException(status_code=403, detail="Sem permissão")

    prescricao = db.query(m.Receita).filter(m.Receita.id == prescricao_id).first()  # Consulta prescrição
    if not prescricao:
        raise HTTPException(status_code=404, detail="Prescrição não encontrada")

    prescricao.status = "CANCELADA"  # Altera status
    db.commit()  # Salva alterações
    db.refresh(prescricao)  # Atualiza objeto

    registrar_log(
        db=db,
        usuario_email=usuario_atual.get("email"),
        tabela="Receita",
        registro_id=prescricao.id,
        acao="DELETE",
        detalhes=f"Prescrição {prescricao_id} cancelada pelo usuário {usuario_atual.get('email')}"
    )

    return prescricao  # Retorna prescrição cancelada
