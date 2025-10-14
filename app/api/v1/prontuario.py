import os
from fastapi import APIRouter, Depends, HTTPException, status, Form, UploadFile, File, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.db import get_db
from app import models as m
from app.core import security
from app.schemas.prontuario import ProntuarioMedicoResponse
from app.utils.logs import registrar_log

roteador = APIRouter()

# Diretório onde arquivos enviados serão salvos
UPLOAD_DIR = "app/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ============================================================
# FUNÇÃO AUXILIAR: Obter usuário atual
# ============================================================
def obter_usuario_atual(
        current_user=Depends(security.get_current_user),
        db: Session = Depends(get_db)
):
    """
    Garante que o usuário autenticado tenha o campo 'email' disponível.
    Evita falhas nos logs quando o token JWT não contém o email.
    """
    usuario_email = current_user.get("email")
    if not usuario_email:
        usuario = db.query(m.Usuario).filter(m.Usuario.id == int(current_user.get("id"))).first()
        if usuario:
            usuario_email = usuario.email
            current_user["email"] = usuario.email
    return current_user


# ============================================================
# ENDPOINT: Criar prontuário
# ============================================================
@roteador.post("/prontuarios", response_model=ProntuarioMedicoResponse, status_code=status.HTTP_201_CREATED)
def criar_prontuario(
        request: Request,
        paciente_id: int = Form(...),
        medico_id: int = Form(...),
        descricao: str = Form(...),
        arquivo: Optional[UploadFile] = File(None),
        db: Session = Depends(get_db),
        usuario_atual=Depends(obter_usuario_atual)
):
    """
    Cria um novo prontuário médico para um paciente.

    - **Acesso:** apenas MEDICO ou ADMIN
    - Suporte para upload de arquivo opcional
    - **Registra log** da operação
    """
    if usuario_atual.get("papel") not in ["MEDICO", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Sem permissão")

    caminho_arquivo = None
    if arquivo:
        nome_arquivo = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{arquivo.filename}"
        caminho_arquivo = os.path.join(UPLOAD_DIR, nome_arquivo)
        with open(caminho_arquivo, "wb") as buffer:
            buffer.write(arquivo.file.read())

    novo_prontuario = m.Prontuario(
        paciente_id=paciente_id,
        medico_id=medico_id,
        descricao=descricao,
        data_hora=datetime.now(),
        status="ATIVO",
        anexo=caminho_arquivo
    )

    db.add(novo_prontuario)
    db.commit()
    db.refresh(novo_prontuario)

    registrar_log(
        db=db,
        usuario_email=usuario_atual.get("email"),
        tabela="Prontuario",
        registro_id=novo_prontuario.id,
        acao="CREATE",
        detalhes=f"Prontuário criado para paciente {paciente_id} pelo médico {medico_id}"
                 + (f" com anexo {arquivo.filename}" if arquivo else "")
    )

    anexo_url = None
    if novo_prontuario.anexo:
        nome_arquivo = os.path.basename(novo_prontuario.anexo)
        base_url = str(request.base_url).rstrip("/")
        anexo_url = f"{base_url}/uploads/{nome_arquivo}"

    return ProntuarioMedicoResponse(
        id=novo_prontuario.id,
        paciente_id=novo_prontuario.paciente_id,
        medico_id=novo_prontuario.medico_id,
        descricao=novo_prontuario.descricao,
        data_hora=novo_prontuario.data_hora,
        anexo=anexo_url
    )


# ============================================================
# ENDPOINT: Listar prontuários
# ============================================================
@roteador.get("/prontuarios", response_model=List[ProntuarioMedicoResponse])
def listar_prontuarios(
        request: Request,
        db: Session = Depends(get_db),
        usuario_atual=Depends(obter_usuario_atual)
):
    """
    Lista todos os prontuários médicos cadastrados.

    - **Acesso:** apenas MEDICO ou ADMIN
    - Retorna URLs públicas para anexos, se existirem
    - **Registra log** da operação
    """
    if usuario_atual.get("papel") not in ["MEDICO", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Sem permissão")

    prontuarios = db.query(m.Prontuario).all()
    base_url = str(request.base_url).rstrip("/")

    lista_formatada = []
    for p in prontuarios:
        anexo_url = None
        if getattr(p, "anexo", None):
            nome_arquivo = os.path.basename(p.anexo)
            anexo_url = f"{base_url}/uploads/{nome_arquivo}"

        lista_formatada.append(ProntuarioMedicoResponse(
            id=p.id,
            paciente_id=p.paciente_id,
            medico_id=p.medico_id,
            descricao=p.descricao,
            data_hora=p.data_hora,
            anexo=anexo_url
        ))

    registrar_log(
        db=db,
        usuario_email=usuario_atual.get("email"),
        tabela="Prontuario",
        acao="READ",
        detalhes=f"{usuario_atual.get('email')} listou todos os prontuários"
    )

    return lista_formatada


# ============================================================
# ENDPOINT: Cancelar prontuário
# ============================================================
@roteador.post("/prontuarios/{prontuario_id}/cancelar", response_model=ProntuarioMedicoResponse)
def cancelar_prontuario(
        prontuario_id: int,
        request: Request,
        db: Session = Depends(get_db),
        usuario_atual=Depends(obter_usuario_atual)
):
    """
    Cancela um prontuário médico existente.

    - **Acesso:** apenas MEDICO ou ADMIN
    - Altera status do prontuário para 'CANCELADO'
    - Retorna URL pública do anexo se existir
    - **Registra log** da operação
    """
    if usuario_atual.get("papel") not in ["MEDICO", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Sem permissão")

    prontuario = db.query(m.Prontuario).filter(m.Prontuario.id == prontuario_id).first()
    if not prontuario:
        raise HTTPException(status_code=404, detail="Prontuário não encontrado")

    prontuario.status = "CANCELADO"
    db.commit()
    db.refresh(prontuario)

    registrar_log(
        db=db,
        usuario_email=usuario_atual.get("email"),
        tabela="Prontuario",
        registro_id=prontuario.id,
        acao="DELETE",
        detalhes=f"Prontuário {prontuario_id} cancelado pelo usuário {usuario_atual.get('email')}"
    )

    anexo_url = None
    if getattr(prontuario, "anexo", None):
        nome_arquivo = os.path.basename(prontuario.anexo)
        base_url = str(request.base_url).rstrip("/")
        anexo_url = f"{base_url}/uploads/{nome_arquivo}"

    return ProntuarioMedicoResponse(
        id=prontuario.id,
        paciente_id=prontuario.paciente_id,
        medico_id=prontuario.medico_id,
        descricao=prontuario.descricao,
        data_hora=prontuario.data_hora,
        anexo=anexo_url
    )
