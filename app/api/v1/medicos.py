from fastapi import APIRouter, Depends, HTTPException, status, Form  # Importações FastAPI
from sqlalchemy.orm import Session  # Sessão do SQLAlchemy
from typing import List, Optional  # Tipagens
from app.db import get_db  # Função para obter sessão do banco
from app import models as m  # Import dos models
from app.core import security  # Autenticação e segurança
from app.schemas.medico import MedicoResponse  # Schema de resposta para médico
from app.utils.logs import registrar_log  # Função de log de auditoria

roteador = APIRouter()  # Cria o roteador FastAPI


# ----------------------------
# Obter usuário atual com email garantido
# ----------------------------
def obter_usuario_atual(
        current_user=Depends(security.get_current_user),  # Usuário obtido via token
        db: Session = Depends(get_db)  # Sessão do banco
):
    """
    Retorna o usuário autenticado com email garantido.
    Evita falhas nos logs quando o token JWT não contém o campo 'email'.
    """
    usuario_email = current_user.get("email")  # Tenta obter o email do token
    if not usuario_email:  # Se não existir, busca no banco
        usuario = db.query(m.Usuario).filter(m.Usuario.id == int(current_user.get("id"))).first()
        if usuario:
            usuario_email = usuario.email
            current_user["email"] = usuario.email
    return current_user  # Retorna usuário com email


# ----------------------------
# Criar médico
# ----------------------------
@roteador.post("/", response_model=MedicoResponse, status_code=status.HTTP_201_CREATED)
def criar_medico(
        nome: str = Form(...),  # Nome do médico
        email: str = Form(...),  # Email do médico
        telefone: Optional[str] = Form(None),  # Telefone opcional
        crm: str = Form(...),  # CRM obrigatório
        especialidade: Optional[str] = Form(None),  # Especialidade opcional
        db: Session = Depends(get_db),
        usuario_atual=Depends(obter_usuario_atual)
):
    """
    Cria um novo médico.
    Apenas ADMIN pode criar médicos.
    Verifica duplicidade de email e CRM antes de criar.
    """
    if usuario_atual.get("papel") != "ADMIN":  # Verifica permissão
        raise HTTPException(status_code=403, detail="Apenas ADMIN pode criar médicos")

    if db.query(m.Medico).filter(m.Medico.email == email).first():  # Verifica email duplicado
        raise HTTPException(status_code=400, detail="Email já cadastrado")
    if db.query(m.Medico).filter(m.Medico.crm == crm).first():  # Verifica CRM duplicado
        raise HTTPException(status_code=400, detail="CRM já cadastrado")

    novo_medico = m.Medico(  # Cria objeto médico
        nome=nome,
        email=email,
        telefone=telefone,
        crm=crm,
        especialidade=especialidade
    )
    db.add(novo_medico)  # Adiciona à sessão
    db.commit()  # Salva alterações
    db.refresh(novo_medico)  # Atualiza objeto com ID

    registrar_log(  # Log detalhado
        db=db,
        usuario_email=usuario_atual.get("email"),
        tabela="medicos",
        registro_id=novo_medico.id,
        acao="CREATE",
        detalhes=f"Médico criado: {novo_medico.nome} por {usuario_atual.get('email')}"
    )

    return novo_medico  # Retorna objeto criado


# ----------------------------
# Listar médicos
# ----------------------------
@roteador.get("/", response_model=List[MedicoResponse])
def listar_medicos(
        pagina: int = 1,  # Página inicial
        tamanho: int = 20,  # Tamanho da página
        db: Session = Depends(get_db),
        usuario_atual=Depends(obter_usuario_atual)
):
    """
    Lista médicos com paginação.
    Apenas usuários ADMIN ou MEDICO podem acessar.
    """
    if usuario_atual.get("papel") not in ["ADMIN", "MEDICO"]:  # Verifica permissão
        raise HTTPException(status_code=403, detail="Sem permissão")

    medicos = db.query(m.Medico).offset((pagina - 1) * tamanho).limit(tamanho).all()  # Consulta paginada

    registrar_log(  # Log de auditoria
        db=db,
        usuario_email=usuario_atual.get("email"),
        tabela="medicos",
        acao="READ",
        detalhes=f"{usuario_atual.get('email')} listou médicos (página {pagina})"
    )

    return medicos  # Retorna lista de médicos


# ----------------------------
# Obter médico por ID
# ----------------------------
@roteador.get("/{medico_id}", response_model=MedicoResponse)
def obter_medico(
        medico_id: int,  # ID do médico
        db: Session = Depends(get_db),
        usuario_atual=Depends(obter_usuario_atual)
):
    """
    Retorna os dados de um médico específico pelo ID.
    Apenas ADMIN ou MEDICO podem acessar.
    """
    if usuario_atual.get("papel") not in ["ADMIN", "MEDICO"]:  # Verifica permissão
        raise HTTPException(status_code=403, detail="Sem permissão")

    medico = db.query(m.Medico).filter(m.Medico.id == medico_id).first()  # Consulta médico
    if not medico:
        raise HTTPException(status_code=404, detail="Médico não encontrado")

    registrar_log(  # Log detalhado
        db=db,
        usuario_email=usuario_atual.get("email"),
        tabela="medicos",
        registro_id=medico.id,
        acao="READ",
        detalhes=f"{usuario_atual.get('email')} acessou médico ID {medico.id}"
    )

    return medico  # Retorna médico


# ----------------------------
# Atualizar médico
# ----------------------------
@roteador.put("/{medico_id}", response_model=MedicoResponse)
def atualizar_medico(
        medico_id: int,  # ID do médico
        nome: Optional[str] = None,
        email: Optional[str] = None,
        telefone: Optional[str] = None,
        crm: Optional[str] = None,
        especialidade: Optional[str] = None,
        db: Session = Depends(get_db),
        usuario_atual=Depends(obter_usuario_atual)
):
    """
    Atualiza os dados de um médico existente.
    Apenas ADMIN pode atualizar médicos.
    Campos não fornecidos permanecem inalterados.
    """
    if usuario_atual.get("papel") != "ADMIN":  # Verifica permissão
        raise HTTPException(status_code=403, detail="Apenas ADMIN pode atualizar médicos")

    db_medico = db.query(m.Medico).filter(m.Medico.id == medico_id).first()  # Consulta médico
    if not db_medico:
        raise HTTPException(status_code=404, detail="Médico não encontrado")

    # Atualiza campos se fornecidos
    if nome is not None:
        db_medico.nome = nome
    if email is not None:
        db_medico.email = email
    if telefone is not None:
        db_medico.telefone = telefone
    if crm is not None:
        db_medico.crm = crm
    if especialidade is not None:
        db_medico.especialidade = especialidade

    db.commit()  # Salva alterações
    db.refresh(db_medico)  # Atualiza objeto

    registrar_log(  # Log detalhado
        db=db,
        usuario_email=usuario_atual.get("email"),
        tabela="medicos",
        registro_id=medico_id,
        acao="UPDATE",
        detalhes=f"Médico atualizado: {db_medico.nome} por {usuario_atual.get('email')}"
    )

    return db_medico  # Retorna médico atualizado


# ----------------------------
# Excluir médico (soft-delete)
# ----------------------------
@roteador.delete("/{medico_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_medico(
        medico_id: int,  # ID do médico
        db: Session = Depends(get_db),
        usuario_atual=Depends(obter_usuario_atual)
):
    """
    Inativa um médico (soft-delete) em vez de excluir permanentemente.
    Apenas ADMIN pode realizar esta operação.
    """
    if usuario_atual.get("papel") != "ADMIN":  # Verifica permissão
        raise HTTPException(status_code=403, detail="Apenas ADMIN pode excluir médicos")

    db_medico = db.query(m.Medico).filter(m.Medico.id == medico_id).first()  # Consulta médico
    if not db_medico:
        raise HTTPException(status_code=404, detail="Médico não encontrado")

    db_medico.ativo = False  # Marca como inativo
    db.commit()  # Salva alteração

    registrar_log(  # Log detalhado
        db=db,
        usuario_email=usuario_atual.get("email"),
        tabela="medicos",
        registro_id=medico_id,
        acao="DELETE",
        detalhes=f"Médico excluído (inativado): {db_medico.nome} por {usuario_atual.get('email')}"
    )

    return None  # Retorna None (204 No Content)
