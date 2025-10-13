# D:\ProjectSGHSS\app\api\v1\auditoria.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.models.audit import AuditLog
from app.core import security

roteador = APIRouter()


# --------------------------
# Obter usuário atual com email garantido
# --------------------------
def obter_usuario_atual(
        current_user=Depends(security.get_current_user),
        db: Session = Depends(get_db)
):
    """
    🔐 **Obter Usuário Atual**

    Garante que o usuário autenticado tenha o campo `email` disponível no token.
    Caso o token JWT não contenha o e-mail, ele é recuperado do banco de dados
    a partir do ID do usuário.

    Retorna:
        dict: Dados do usuário autenticado com o campo `email` garantido.
    """
    usuario_email = current_user.get("email")

    # Caso o e-mail não esteja presente no token JWT
    if not usuario_email:
        from app import models as m
        usuario = db.query(m.Usuario).filter(m.Usuario.id == int(current_user.get("id"))).first()

        # Se o usuário for encontrado no banco, atualiza o e-mail no contexto atual
        if usuario:
            usuario_email = usuario.email
            current_user["email"] = usuario.email

    return current_user


# --------------------------
# Listar logs de auditoria
# --------------------------
@roteador.get("/audit_logs", summary="Listar logs de auditoria", tags=["Auditoria"])
def listar_logs(
        usuario_atual=Depends(obter_usuario_atual),
        db: Session = Depends(get_db)
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

    # Retorna os dados formatados como dicionários
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
