# D:\ProjectSGHSS\app\api\v1\prontuario.py
from fastapi import APIRouter, Depends, HTTPException, status, Form, UploadFile, File  # FastAPI imports
from sqlalchemy.orm import Session  # Sessão do SQLAlchemy
from typing import List, Optional  # Tipagem
from pathlib import Path  # Manipulação de diretórios/arquivos
from datetime import datetime  # Para timestamp

from app.db import get_db  # Função para obter sessão do banco
from app import models as m  # Import dos models
from app.core import security  # Autenticação e segurança
from app.schemas import ProntuarioResponse  # Schema de resposta de prontuário
from app.utils.logs import registrar_log  # Função utilitária para logs

roteador = APIRouter()  # Criação do roteador FastAPI


# ============================================================
# FUNÇÃO AUXILIAR: Obter usuário atual
# ============================================================
def obter_usuario_atual(
        current_user=Depends(security.get_current_user),  # Usuário via token JWT
        db: Session = Depends(get_db)  # Sessão do banco
):
    """
    Garante que o usuário autenticado possua o campo 'email'.
    Evita falhas nos logs quando o token JWT não contém email.
    """
    usuario_email = current_user.get("email")  # Tenta obter email do token
    if not usuario_email:  # Se não houver, busca no banco
        usuario = db.query(m.Usuario).filter(m.Usuario.id == int(current_user.get("id"))).first()
        if usuario:
            usuario_email = usuario.email
            current_user["email"] = usuario.email
    return current_user  # Retorna usuário com email garantido


# ============================================================
# ENDPOINT: Criar Prontuário
# ============================================================
@roteador.post("/", response_model=ProntuarioResponse, status_code=status.HTTP_201_CREATED)
async def criar_prontuario(
        paciente_id: int = Form(...),  # ID do paciente
        medico_id: int = Form(...),  # ID do médico
        descricao: Optional[str] = Form(None),  # Observações/descrição
        arquivo: Optional[UploadFile] = File(None),  # Arquivo anexo opcional
        db: Session = Depends(get_db),
        usuario_atual=Depends(obter_usuario_atual)
):
    """
    Cria um novo prontuário.
    Apenas ADMIN ou MEDICO podem criar prontuários.
    """
    # ----------------------------
    # Verifica permissão
    # ----------------------------
    if usuario_atual.get("papel") not in ["ADMIN", "MEDICO"]:
        raise HTTPException(status_code=403, detail="Sem permissão")

    # ----------------------------
    # Verifica se paciente e médico existem
    # ----------------------------
    paciente = db.query(m.Paciente).filter(m.Paciente.id == paciente_id).first()
    medico = db.query(m.Medico).filter(m.Medico.id == medico_id).first()

    if not paciente or not medico:
        raise HTTPException(status_code=404, detail="Paciente ou médico não encontrado")

    # ----------------------------
    # Se houver arquivo, salva em diretório local
    # ----------------------------
    caminho_arquivo = None
    if arquivo:
        diretorio_upload = Path("uploads/prontuarios")  # Define pasta de uploads
        diretorio_upload.mkdir(parents=True, exist_ok=True)  # Cria se não existir
        caminho_arquivo = diretorio_upload / arquivo.filename
        with open(caminho_arquivo, "wb") as f:
            f.write(await arquivo.read())  # Grava o arquivo

    # ----------------------------
    # Criação do prontuário
    # ----------------------------
    novo = m.Prontuario(
        paciente_id=paciente_id,
        medico_id=medico_id,
        descricao=descricao,
        data_hora=datetime.now(),  # Timestamp atual
        anexo=str(caminho_arquivo) if caminho_arquivo else None  # Salva caminho do arquivo se existir
    )

    db.add(novo)  # Adiciona à sessão
    db.commit()  # Salva no banco
    db.refresh(novo)  # Atualiza objeto com ID gerado

    # ----------------------------
    # Registro de auditoria
    # ----------------------------
    registrar_log(
        db=db,
        usuario_email=usuario_atual.get("email"),
        tabela="prontuarios",
        registro_id=novo.id,
        acao="CREATE",
        detalhes=f"Prontuário criado para o paciente {paciente.nome} por {usuario_atual.get('email')}"
    )

    return novo  # Retorna prontuário criado


# ============================================================
# ENDPOINT: Listar prontuários
# ============================================================
@roteador.get("/", response_model=List[ProntuarioResponse])
def listar_prontuarios(
        db: Session = Depends(get_db),
        usuario_atual=Depends(obter_usuario_atual)
):
    """
    Lista todos os prontuários cadastrados.

    - **Acesso:** apenas MÉDICO ou ADMIN
    - **Registra log** da operação
    """
    if usuario_atual.get("papel") not in ["MEDICO", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Sem permissão")

    prontuarios = db.query(m.Prontuario).all()  # Consulta todos os prontuários

    registrar_log(
        db=db,
        usuario_email=usuario_atual.get("email"),
        tabela="Prontuario",
        registro_id=None,
        acao="READ",
        detalhes=f"{usuario_atual.get('email')} listou todos os prontuários"
    )

    return prontuarios  # Retorna lista de prontuários


# ============================================================
# ENDPOINT: Excluir (ou cancelar) prontuário
# ============================================================
@roteador.delete("/{prontuario_id}", response_model=ProntuarioResponse)
def excluir_prontuario(
        prontuario_id: int,  # ID do prontuário
        db: Session = Depends(get_db),
        usuario_atual=Depends(obter_usuario_atual)
):
    """
    Exclui um prontuário existente pelo ID.

    - **Acesso:** apenas ADMIN
    - **Registra log** da operação
    """
    if usuario_atual.get("papel") != "ADMIN":
        raise HTTPException(status_code=403, detail="Sem permissão")

    prontuario = db.query(m.Prontuario).filter(m.Prontuario.id == prontuario_id).first()
    if not prontuario:
        raise HTTPException(status_code=404, detail="Prontuário não encontrado")

    db.delete(prontuario)  # Remove do banco
    db.commit()  # Salva alterações

    registrar_log(
        db=db,
        usuario_email=usuario_atual.get("email"),
        tabela="Prontuario",
        registro_id=prontuario_id,
        acao="DELETE",
        detalhes=f"Prontuário {prontuario_id} excluído por {usuario_atual.get('email')}"
    )

    return prontuario  # Retorna prontuário excluído
