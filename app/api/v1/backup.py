import shutil
import os
from datetime import datetime
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.db import get_db
from app import models as m
from app.core import security
from app.utils.logs import registrar_log

# ----------------------------
# Criação do roteador principal
# ----------------------------
roteador = APIRouter()

# Diretório onde os arquivos de backup serão armazenados
BACKUP_DIR = "backups"
os.makedirs(BACKUP_DIR, exist_ok=True)  # Garante que a pasta exista


# ----------------------------
# Obter usuário atual com email garantido
# ----------------------------
def obter_usuario_atual(
        current_user=Depends(security.get_current_user),
        db: Session = Depends(get_db)
):
    """
    📘 **Obter Usuário Atual com Email Garantido**

    Retorna o usuário autenticado a partir do token JWT,
    garantindo que o campo `email` esteja presente.
    Caso o token não contenha o email, ele é buscado no banco.

    **Retorna:**
    - `dict`: Dados do usuário autenticado
    """
    usuario_email = current_user.get("email")
    if not usuario_email:
        usuario = db.query(m.Usuario).filter(m.Usuario.id == int(current_user.get("id"))).first()
        if usuario:
            usuario_email = usuario.email
            current_user["email"] = usuario.email
    return current_user


# ----------------------------
# Gerar backup do banco de dados
# ----------------------------
@roteador.get("/exportar", summary="Gerar backup do banco de dados", tags=["Backup e Restauração"])
def gerar_backup(
        db: Session = Depends(get_db),
        usuario_atual=Depends(obter_usuario_atual)
):
    """
    💾 **Gerar Backup do Banco de Dados**

    Gera uma cópia completa do banco de dados atual e disponibiliza
    o arquivo `.db` para download.

    **Somente usuários ADMIN podem executar esta ação.**

    **Retorno:**
    - Arquivo `.db` com o backup completo.

    **Exemplo de uso:**
    GET /api/v1/backup/exportar
    """
    if usuario_atual["papel"] != "ADMIN":
        raise HTTPException(status_code=403, detail="Acesso negado: apenas ADMIN")

    nome_arquivo = f"sghss_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    caminho_destino = os.path.join(BACKUP_DIR, nome_arquivo)

    shutil.copy("sghss.db", caminho_destino)

    registrar_log(
        db,
        usuario_atual["email"],
        "Backup",
        acao="CREATE",
        detalhes=f"Backup gerado: {nome_arquivo}"
    )

    return FileResponse(
        caminho_destino,
        filename=nome_arquivo,
        media_type="application/octet-stream"
    )


# ----------------------------
# Restaurar banco de dados a partir de um backup
# ----------------------------
@roteador.post("/importar", summary="Restaurar banco de dados", tags=["Backup e Restauração"])
def restaurar_backup(
        arquivo: UploadFile = File(..., description="Arquivo .db de backup para restaurar"),
        db: Session = Depends(get_db),
        usuario_atual=Depends(obter_usuario_atual)
):
    """
    🔄 **Restaurar Banco de Dados a partir de um Backup**

    Permite restaurar o banco de dados do sistema a partir de um arquivo `.db` de backup.
    O arquivo enviado substituirá o banco de dados atual.

    **Somente usuários ADMIN podem executar esta ação.**

    **Parâmetros:**
    - `arquivo`: arquivo `.db` do backup (enviado via formulário)

    **Retorno:**
    - Mensagem de sucesso confirmando a restauração

    **Exemplo de uso:**
    POST /api/v1/backup/importar
    """
    if usuario_atual["papel"] != "ADMIN":
        raise HTTPException(status_code=403, detail="Acesso negado: apenas ADMIN")

    if not arquivo.filename.endswith(".db"):
        raise HTTPException(status_code=400, detail="Arquivo inválido. Envie um .db")

    caminho_temp = os.path.join(BACKUP_DIR, arquivo.filename)

    with open(caminho_temp, "wb") as buffer:
        buffer.write(arquivo.file.read())

    shutil.copy(caminho_temp, "sghss.db")

    registrar_log(
        db,
        usuario_atual["email"],
        "Backup",
        acao="UPDATE",
        detalhes=f"Banco restaurado a partir de {arquivo.filename}"
    )

    return {"detail": "Banco de dados restaurado com sucesso"}
