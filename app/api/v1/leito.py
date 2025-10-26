from fastapi import APIRouter, Depends, HTTPException, status, Form  # Importações FastAPI
from sqlalchemy.orm import Session  # Sessão do SQLAlchemy
from typing import List, Optional  # Tipagens
from app.db import get_db  # Função para obter sessão do banco
from app import models as m  # Import dos models
from app.core import security  # Autenticação e segurança
from pydantic import BaseModel  # BaseModel Pydantic
from app.utils.logs import registrar_log  # Função de log de auditoria


# ============================================================
# SCHEMAS
# ============================================================
class LeitoBase(BaseModel):
    """
    Schema base para criação ou atualização de um leito.
    """
    numero: str  # Número do leito
    status: str  # Status do leito (Livre, Ocupado, etc.)
    paciente_id: Optional[int] = None  # ID do paciente associado (opcional)


class LeitoResponse(LeitoBase):
    """
    Schema de resposta de um leito, incluindo o ID.
    Compatível com objetos SQLAlchemy (from_attributes=True).
    """
    id: int  # ID do leito
    model_config = {"from_attributes": True}  # Pydantic v2, permite instanciar a partir de objetos SQLAlchemy


# ============================================================
# ROTEADOR
# ============================================================
roteador = APIRouter()  # Cria o roteador FastAPI


# ============================================================
# FUNÇÃO AUXILIAR: Obter usuário autenticado
# ============================================================
def obter_usuario_atual(
        current_user=Depends(security.get_current_user),  # Usuário obtido via token
        db: Session = Depends(get_db)  # Sessão do banco
):
    """
    Obtém o usuário autenticado, garantindo que o campo `email` esteja presente
    no token JWT ou seja buscado no banco de dados.
    """
    usuario_email = current_user.get("email")  # Tenta obter o email do token
    if not usuario_email:
        usuario = db.query(m.Usuario).filter(m.Usuario.id == int(current_user.get("id"))).first()
        if usuario:
            usuario_email = usuario.email
            current_user["email"] = usuario.email
    return current_user


# ============================================================
# ENDPOINT: CRIAR LEITO
# ============================================================
@roteador.post(
    "/leitos",
    response_model=LeitoResponse,  # Retorna schema LeitoResponse
    status_code=status.HTTP_201_CREATED
)
def criar_leito(
        numero: str = Form(..., description="Número identificador do leito", example="101"),
        status_leito: str = Form(..., description="Status atual do leito (Livre, Ocupado, Manutenção)",
                                 example="Livre"),
        paciente_id: Optional[int] = Form(None, description="ID do paciente associado (opcional)"),
        db: Session = Depends(get_db),
        usuario_atual=Depends(obter_usuario_atual)
):
    """
    Cria um novo leito hospitalar.

    - **Acesso:** apenas ADMIN
    - **Campos obrigatórios:** numero, status
    - **Campos opcionais:** paciente_id
    """
    if usuario_atual.get("papel") != "ADMIN":  # Verifica permissão
        raise HTTPException(status_code=403, detail="Acesso negado: apenas ADMIN pode criar leitos")

    novo_leito = m.Leito(  # Cria objeto Leito
        numero=numero,
        status=status_leito,
        paciente_id=paciente_id
    )

    db.add(novo_leito)  # Adiciona à sessão
    db.commit()  # Salva alterações
    db.refresh(novo_leito)  # Atualiza objeto com ID

    registrar_log(  # Log de auditoria
        db,
        usuario_atual["email"],
        "Leito",
        registro_id=novo_leito.id,
        acao="CREATE",
        detalhes=f"Leito {numero} criado com status {status_leito}"
    )

    return novo_leito  # Retorna objeto criado


# ============================================================
# ENDPOINT: LISTAR LEITOS
# ============================================================
@roteador.get(
    "/leitos",
    response_model=List[LeitoResponse]  # Lista de leitos
)
def listar_leitos(
        db: Session = Depends(get_db),
        usuario_atual=Depends(obter_usuario_atual)
):
    """
    Lista todos os leitos cadastrados.

    - **Acesso:** ADMIN ou MEDICO
    """
    if usuario_atual.get("papel") not in ["ADMIN", "MEDICO"]:  # Permissões
        raise HTTPException(status_code=403, detail="Acesso negado")

    leitos = db.query(m.Leito).all()  # Consulta todos os leitos

    registrar_log(  # Log de listagem
        db,
        usuario_atual["email"],
        "Leito",
        acao="READ",
        detalhes="Listagem de leitos"
    )

    return leitos  # Retorna lista


# ============================================================
# ENDPOINT: ATUALIZAR LEITO
# ============================================================
@roteador.patch(
    "/leitos/{leito_id}",
    response_model=LeitoResponse  # Retorna objeto atualizado
)
def atualizar_leito(
        leito_id: int,
        numero: Optional[str] = Form(None, description="Número identificador do leito", example="101"),
        status_leito: Optional[str] = Form(None, description="Status atual do leito", example="Livre"),
        paciente_id: Optional[int] = Form(None, description="ID do paciente associado", example=None),
        db: Session = Depends(get_db),
        usuario_atual=Depends(obter_usuario_atual)
):
    """
    Atualiza os campos de um leito existente.

    - **Acesso:** apenas ADMIN
    - **Campos opcionais:** numero, status, paciente_id
    """
    if usuario_atual.get("papel") != "ADMIN":  # Verifica permissão
        raise HTTPException(status_code=403, detail="Acesso negado")

    leito = db.query(m.Leito).filter(m.Leito.id == leito_id).first()  # Busca leito
    if not leito:
        raise HTTPException(status_code=404, detail="Leito não encontrado")

    if numero is not None:
        leito.numero = numero  # Atualiza número
    if status_leito is not None:
        leito.status = status_leito  # Atualiza status
    if paciente_id is not None:
        leito.paciente_id = paciente_id  # Atualiza paciente

    db.commit()  # Salva alterações
    db.refresh(leito)  # Atualiza objeto

    registrar_log(  # Log de auditoria
        db,
        usuario_atual["email"],
        "Leito",
        registro_id=leito.id,
        acao="UPDATE",
        detalhes=f"Leito {leito_id} atualizado"
    )

    return leito  # Retorna objeto atualizado


# ============================================================
# ENDPOINT: EXCLUIR LEITO
# ============================================================
@roteador.delete(
    "/leitos/{leito_id}",
    status_code=status.HTTP_200_OK
)
def excluir_leito(
        leito_id: int,
        db: Session = Depends(get_db),
        usuario_atual=Depends(obter_usuario_atual)
):
    """
    Exclui um leito pelo ID.

    - **Acesso:** apenas ADMIN
    """
    if usuario_atual.get("papel") != "ADMIN":  # Verifica permissão
        raise HTTPException(status_code=403, detail="Acesso negado: apenas ADMIN pode excluir leitos")

    leito = db.query(m.Leito).filter(m.Leito.id == leito_id).first()  # Busca leito
    if not leito:
        raise HTTPException(status_code=404, detail="Leito não encontrado")

    db.delete(leito)  # Remove da sessão
    db.commit()  # Salva alterações

    registrar_log(  # Log de auditoria
        db,
        usuario_atual["email"],
        "Leito",
        registro_id=leito_id,
        acao="DELETE",
        detalhes=f"Leito excluído ID {leito_id} por {usuario_atual.get('email')}"
    )

    return {"detail": "Leito excluído com sucesso"}  # Confirmação
