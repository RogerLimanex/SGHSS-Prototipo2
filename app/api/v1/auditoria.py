from fastapi import APIRouter, Depends, HTTPException  # Importa funcionalidades do FastAPI
from sqlalchemy.orm import Session  # Importa sessão do SQLAlchemy para consultas
from app.db import get_db  # Função para obter sessão do banco
from app.models.audit import AuditLog  # Modelo de logs de auditoria
from app.core import security  # Funções de segurança (ex: JWT, autenticação)

roteador = APIRouter()  # Cria o roteador FastAPI para este módulo


# --------------------------
# Obter usuário atual com email garantido
# --------------------------
def obter_usuario_atual(
        current_user=Depends(security.get_current_user),  # Recupera o usuário do token JWT
        db: Session = Depends(get_db)  # Injeção de dependência da sessão do banco
):
    """
    🔐 **Obter Usuário Atual**

    Garante que o usuário autenticado tenha o campo `email` disponível no token.
    Caso o token JWT não contenha o e-mail, ele é recuperado do banco de dados
    a partir do ID do usuário.

    Retorna:
        dict: Dados do usuário autenticado com o campo `email` garantido.
    """
    usuario_email = current_user.get("email")  # Tenta obter email do token

    # Caso o e-mail não esteja presente no token JWT
    if not usuario_email:
        from app import models as m  # Importa modelos dinamicamente
        usuario = db.query(m.Usuario).filter(m.Usuario.id == int(current_user.get("id"))).first()

        # Se o usuário for encontrado no banco, atualiza o e-mail no contexto atual
        if usuario:
            usuario_email = usuario.email
            current_user["email"] = usuario.email  # Atualiza email no objeto do usuário

    return current_user  # Retorna dados do usuário com email garantido


# --------------------------
# Listar logs de auditoria
# --------------------------
@roteador.get("/audit_logs", summary="Listar logs de auditoria", tags=["Auditoria"])
def listar_logs(
        usuario_atual=Depends(obter_usuario_atual),  # Obtém usuário autenticado
        db: Session = Depends(get_db)  # Sessão do banco
):
    """
    📋 **Listar Logs de Auditoria**

    Retorna todos os registros de auditoria do sistema, exibindo detalhes
    sobre as ações realizadas pelos usuários.

    **Acesso:** Somente ADMIN.

    Campos retornados:
    * `id` → Identificador do log
    * `usuario_email` → Usuário responsável pela ação
    * `tabela` → Nome da tabela afetada
    * `registro_id` → ID do registro alterado
    * `acao` → Tipo de ação (CREATE, READ, UPDATE, DELETE)
    * `detalhes` → Descrição da ação executada
    * `data_hora` → Data e hora da operação
    """
    # Verifica se o usuário possui permissão de administrador
    if usuario_atual.get("papel") != "ADMIN":
        raise HTTPException(status_code=403, detail="Acesso negado: apenas ADMIN")

    # Busca todos os registros de auditoria em ordem decrescente (mais recentes primeiro)
    logs = db.query(AuditLog).order_by(AuditLog.data_hora.desc()).all()

    # Retorna os dados formatados como lista de dicionários
    return [
        {
            "id": log.id,
            "usuario_email": log.usuario_email,
            "tabela": log.tabela,
            "registro_id": log.registro_id,
            "acao": log.acao,
            "detalhes": log.detalhes,
            "data_hora": log.data_hora,
        }
        for log in logs
    ]
