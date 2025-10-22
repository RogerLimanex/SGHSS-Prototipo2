from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.db import get_db
from app import models as m
from app.core import security
from app.schemas.paciente import PacienteResponse
from app.utils.logs import registrar_log  # Função utilitária para registrar logs

roteador = APIRouter()


# ----------------------------
# Obter usuário atual com email garantido
# ----------------------------
def obter_usuario_atual(
        current_user=Depends(security.get_current_user),
        db: Session = Depends(get_db)
):
    """
    Retorna o usuário autenticado com email garantido.
    Evita falhas nos logs quando o token JWT não contém o campo 'email'.
    """
    usuario_email = current_user.get("email")
    if not usuario_email:
        usuario = db.query(m.Usuario).filter(m.Usuario.id == int(current_user.get("id"))).first()
        if usuario:
            usuario_email = usuario.email
            current_user["email"] = usuario.email
    return current_user


# ----------------------------
# Criar paciente
# ----------------------------
@roteador.post("/", response_model=PacienteResponse, status_code=status.HTTP_201_CREATED)
def criar_paciente(
        nome: str = Form(...),
        email: str = Form(...),
        telefone: Optional[str] = Form(None),
        cpf: str = Form(...),
        data_nascimento: str = Form(...),
        endereco: Optional[str] = Form(None),
        db: Session = Depends(get_db),
        usuario_atual=Depends(obter_usuario_atual)
):
    """
    Cria um novo paciente.
    Apenas ADMIN ou MEDICO podem criar pacientes.
    """

    # -----------------------------------
    # Função auxiliar para tratar formatos de data
    # Aceita: dd/mm/yyyy | dd-mm-yyyy | yyyy-mm-dd
    # -----------------------------------
    def parse_data(data_str: str):
        for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(data_str, fmt).date()
            except ValueError:
                continue
        raise HTTPException(
            status_code=400,
            detail="Data inválida. Use o formato dd/mm/yyyy, dd-mm-yyyy ou yyyy-mm-dd."
        )

    # ----------------------------
    # Validação de permissões
    # ----------------------------
    if usuario_atual.get("papel") not in ["ADMIN", "MEDICO"]:
        raise HTTPException(status_code=403, detail="Sem permissão para criar pacientes")

    # ----------------------------
    # Validação de email duplicado
    # ----------------------------
    if db.query(m.Paciente).filter(m.Paciente.email == email).first():
        raise HTTPException(status_code=400, detail="Email já cadastrado")

    # ----------------------------
    # Criação do novo paciente
    # ----------------------------
    novo = m.Paciente(
        nome=nome,
        email=email,
        telefone=telefone,
        cpf=cpf,
        data_nascimento=parse_data(data_nascimento),
        endereco=endereco
    )

    db.add(novo)
    db.commit()
    db.refresh(novo)

    # ----------------------------
    # Registro de auditoria
    # ----------------------------
    registrar_log(
        db=db,
        usuario_email=usuario_atual.get("email"),
        tabela="pacientes",
        registro_id=novo.id,
        acao="CREATE",
        detalhes=f"Paciente criado: {novo.nome} por {usuario_atual.get('email')}"
    )

    return novo


# ----------------------------
# Listar pacientes
# ----------------------------
@roteador.get("/", response_model=List[PacienteResponse])
def listar_pacientes(
        pagina: int = 1,
        tamanho: int = 20,
        db: Session = Depends(get_db),
        usuario_atual=Depends(obter_usuario_atual)
):
    """
    Lista pacientes com paginação.
    Apenas usuários ADMIN ou MEDICO podem acessar.
    """
    if usuario_atual.get("papel") not in ["ADMIN", "MEDICO"]:
        raise HTTPException(status_code=403, detail="Sem permissão")

    pacientes = db.query(m.Paciente).offset((pagina - 1) * tamanho).limit(tamanho).all()

    registrar_log(
        db=db,
        usuario_email=usuario_atual.get("email"),
        tabela="pacientes",
        acao="READ",
        detalhes=f"{usuario_atual.get('email')} listou pacientes (página {pagina})"
    )

    return pacientes


# ----------------------------
# Obter paciente por ID
# ----------------------------
@roteador.get("/{paciente_id}", response_model=PacienteResponse)
def obter_paciente(
        paciente_id: int,
        db: Session = Depends(get_db),
        usuario_atual=Depends(obter_usuario_atual)
):
    """
    Retorna os dados de um paciente específico pelo ID.
    Apenas ADMIN ou MEDICO podem acessar.
    """
    if usuario_atual.get("papel") not in ["ADMIN", "MEDICO"]:
        raise HTTPException(status_code=403, detail="Sem permissão")

    paciente = db.query(m.Paciente).filter(m.Paciente.id == paciente_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente não encontrado")

    registrar_log(
        db=db,
        usuario_email=usuario_atual.get("email"),
        tabela="pacientes",
        registro_id=paciente.id,
        acao="READ",
        detalhes=f"{usuario_atual.get('email')} acessou paciente ID {paciente.id}"
    )

    return paciente


# ----------------------------
# Atualizar paciente
# ----------------------------
@roteador.put("/{paciente_id}", response_model=PacienteResponse)
def atualizar_paciente(
        paciente_id: int,
        nome: Optional[str] = None,
        email: Optional[str] = None,
        telefone: Optional[str] = None,
        endereco: Optional[str] = None,
        db: Session = Depends(get_db),
        usuario_atual=Depends(obter_usuario_atual)
):
    """
    Atualiza dados de um paciente existente.
    Apenas ADMIN ou MEDICO podem atualizar pacientes.
    Campos não fornecidos permanecem inalterados.
    """
    if usuario_atual.get("papel") not in ["ADMIN", "MEDICO"]:
        raise HTTPException(status_code=403, detail="Sem permissão")

    db_paciente = db.query(m.Paciente).filter(m.Paciente.id == paciente_id).first()
    if not db_paciente:
        raise HTTPException(status_code=404, detail="Paciente não encontrado")

    if nome is not None:
        db_paciente.nome = nome
    if email is not None:
        db_paciente.email = email
    if telefone is not None:
        db_paciente.telefone = telefone
    if endereco is not None:
        db_paciente.endereco = endereco

    db.commit()
    db.refresh(db_paciente)

    registrar_log(
        db=db,
        usuario_email=usuario_atual.get("email"),
        tabela="pacientes",
        registro_id=db_paciente.id,
        acao="UPDATE",
        detalhes=f"Paciente atualizado: {db_paciente.nome} por {usuario_atual.get('email')}"
    )

    return db_paciente


# ----------------------------
# Excluir paciente
# ----------------------------
@roteador.delete("/{paciente_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_paciente(
        paciente_id: int,
        db: Session = Depends(get_db),
        usuario_atual=Depends(obter_usuario_atual)
):
    """
    Exclui um paciente do sistema.
    Apenas ADMIN pode realizar a exclusão.
    """
    if usuario_atual.get("papel") != "ADMIN":
        raise HTTPException(status_code=403, detail="Apenas ADMIN pode excluir")

    db_paciente = db.query(m.Paciente).filter(m.Paciente.id == paciente_id).first()
    if not db_paciente:
        raise HTTPException(status_code=404, detail="Paciente não encontrado")

    db.delete(db_paciente)
    db.commit()

    registrar_log(
        db=db,
        usuario_email=usuario_atual.get("email"),
        tabela="pacientes",
        registro_id=paciente_id,
        acao="DELETE",
        detalhes=f"Paciente excluído ID: {paciente_id} por {usuario_atual.get('email')}"
    )

    return None
