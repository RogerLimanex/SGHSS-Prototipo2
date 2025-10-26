from fastapi import APIRouter, Depends, HTTPException, status, Form  # Importações FastAPI
from sqlalchemy.orm import Session  # Sessão do SQLAlchemy
from typing import List, Optional  # Tipagens
from datetime import datetime  # Para manipulação de datas
from app.db import get_db  # Função para obter sessão do banco
from app import models as m  # Import dos models
from app.core import security  # Autenticação e segurança
from app.schemas.paciente import PacienteResponse  # Schema de resposta para paciente
from app.utils.logs import registrar_log  # Função utilitária para registrar logs

roteador = APIRouter()  # Cria roteador FastAPI


# ----------------------------
# Obter usuário atual com email garantido
# ----------------------------
def obter_usuario_atual(
        current_user=Depends(security.get_current_user),  # Usuário obtido via token JWT
        db: Session = Depends(get_db)  # Sessão do banco
):
    """
    Retorna o usuário autenticado com email garantido.
    Evita falhas nos logs quando o token JWT não contém o campo 'email'.
    """
    usuario_email = current_user.get("email")  # Tenta obter email do token
    if not usuario_email:  # Se não existir, busca no banco
        usuario = db.query(m.Usuario).filter(m.Usuario.id == int(current_user.get("id"))).first()
        if usuario:
            usuario_email = usuario.email
            current_user["email"] = usuario.email
    return current_user  # Retorna usuário com email


# ----------------------------
# Criar paciente
# ----------------------------
@roteador.post("/", response_model=PacienteResponse, status_code=status.HTTP_201_CREATED)
def criar_paciente(
        nome: str = Form(...),  # Nome do paciente
        email: str = Form(...),  # Email do paciente
        telefone: Optional[str] = Form(None),  # Telefone opcional
        cpf: str = Form(...),  # CPF obrigatório
        data_nascimento: str = Form(...),  # Data de nascimento como string
        endereco: Optional[str] = Form(None),  # Endereço opcional
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
        for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"):  # Itera formatos válidos
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
        data_nascimento=parse_data(data_nascimento),  # Converte string para date
        endereco=endereco
    )

    db.add(novo)  # Adiciona à sessão
    db.commit()  # Salva alterações
    db.refresh(novo)  # Atualiza objeto com ID gerado

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

    return novo  # Retorna paciente criado


# ----------------------------
# Listar pacientes
# ----------------------------
@roteador.get("/", response_model=List[PacienteResponse])
def listar_pacientes(
        pagina: int = 1,  # Página inicial
        tamanho: int = 20,  # Tamanho da página
        db: Session = Depends(get_db),
        usuario_atual=Depends(obter_usuario_atual)
):
    """
    Lista pacientes com paginação.
    Apenas usuários ADMIN ou MEDICO podem acessar.
    """
    if usuario_atual.get("papel") not in ["ADMIN", "MEDICO"]:  # Verifica permissão
        raise HTTPException(status_code=403, detail="Sem permissão")

    pacientes = db.query(m.Paciente).offset((pagina - 1) * tamanho).limit(tamanho).all()  # Consulta paginada

    registrar_log(
        db=db,
        usuario_email=usuario_atual.get("email"),
        tabela="pacientes",
        acao="READ",
        detalhes=f"{usuario_atual.get('email')} listou pacientes (página {pagina})"
    )

    return pacientes  # Retorna lista de pacientes


# ----------------------------
# Obter paciente por ID
# ----------------------------
@roteador.get("/{paciente_id}", response_model=PacienteResponse)
def obter_paciente(
        paciente_id: int,  # ID do paciente
        db: Session = Depends(get_db),
        usuario_atual=Depends(obter_usuario_atual)
):
    """
    Retorna os dados de um paciente específico pelo ID.
    Apenas ADMIN ou MEDICO podem acessar.
    """
    if usuario_atual.get("papel") not in ["ADMIN", "MEDICO"]:  # Verifica permissão
        raise HTTPException(status_code=403, detail="Sem permissão")

    paciente = db.query(m.Paciente).filter(m.Paciente.id == paciente_id).first()  # Consulta paciente
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente não encontrado")

    registrar_log(  # Log detalhado
        db=db,
        usuario_email=usuario_atual.get("email"),
        tabela="pacientes",
        registro_id=paciente.id,
        acao="READ",
        detalhes=f"{usuario_atual.get('email')} acessou paciente ID {paciente.id}"
    )

    return paciente  # Retorna paciente


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
    if usuario_atual.get("papel") not in ["ADMIN", "MEDICO"]:  # Verifica permissão
        raise HTTPException(status_code=403, detail="Sem permissão")

    db_paciente = db.query(m.Paciente).filter(m.Paciente.id == paciente_id).first()  # Consulta paciente
    if not db_paciente:
        raise HTTPException(status_code=404, detail="Paciente não encontrado")

    # Atualiza campos fornecidos
    if nome is not None:
        db_paciente.nome = nome
    if email is not None:
        db_paciente.email = email
    if telefone is not None:
        db_paciente.telefone = telefone
    if endereco is not None:
        db_paciente.endereco = endereco

    db.commit()  # Salva alterações
    db.refresh(db_paciente)  # Atualiza objeto

    registrar_log(
        db=db,
        usuario_email=usuario_atual.get("email"),
        tabela="pacientes",
        registro_id=db_paciente.id,
        acao="UPDATE",
        detalhes=f"Paciente atualizado: {db_paciente.nome} por {usuario_atual.get('email')}"
    )

    return db_paciente  # Retorna paciente atualizado


# ----------------------------
# Excluir paciente
# ----------------------------
@roteador.delete("/{paciente_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_paciente(
        paciente_id: int,  # ID do paciente
        db: Session = Depends(get_db),
        usuario_atual=Depends(obter_usuario_atual)
):
    """
    Exclui um paciente do sistema.
    Apenas ADMIN pode realizar a exclusão.
    """
    if usuario_atual.get("papel") != "ADMIN":  # Verifica permissão
        raise HTTPException(status_code=403, detail="Apenas ADMIN pode excluir")

    db_paciente = db.query(m.Paciente).filter(m.Paciente.id == paciente_id).first()  # Consulta paciente
    if not db_paciente:
        raise HTTPException(status_code=404, detail="Paciente não encontrado")

    db.delete(db_paciente)  # Remove paciente
    db.commit()  # Salva alterações

    registrar_log(
        db=db,
        usuario_email=usuario_atual.get("email"),
        tabela="pacientes",
        registro_id=paciente_id,
        acao="DELETE",
        detalhes=f"Paciente excluído ID: {paciente_id} por {usuario_atual.get('email')}"
    )

    return None  # Retorna None (204 No Content)
