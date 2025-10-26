import shutil  # Para cópia de arquivos
import os  # Operações de sistema (diretórios, caminhos)
from datetime import datetime  # Para timestamp do backup
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException  # FastAPI
from fastapi.responses import FileResponse  # Para download de arquivos
from sqlalchemy.orm import Session  # Sessão do SQLAlchemy
from app.db import get_db  # Função para obter sessão do banco
from app import models as m  # Modelos ORM
from app.core import security  # Funções de segurança (JWT, auth)
from app.utils.logs import registrar_log  # Registro de logs de auditoria

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
    """
    if usuario_atual["papel"] != "ADMIN":
        raise HTTPException(status_code=403, detail="Acesso negado: apenas ADMIN")

    # Define nome do arquivo com timestamp
    nome_arquivo = f"sghss_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    caminho_destino = os.path.join(BACKUP_DIR, nome_arquivo)

    # Copia banco de dados atual para backup
    shutil.copy("sghss.db", caminho_destino)

    # Registra log do backup
    registrar_log(
        db,
        usuario_atual["email"],
        "Backup",
        acao="CREATE",
        detalhes=f"Backup gerado: {nome_arquivo}"
    )

    # Retorna arquivo para download
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
    """
    if usuario_atual["papel"] != "ADMIN":
        raise HTTPException(status_code=403, detail="Acesso negado: apenas ADMIN")

    # Valida extensão do arquivo
    if not arquivo.filename.endswith(".db"):
        raise HTTPException(status_code=400, detail="Arquivo inválido. Envie um .db")

    # Salva arquivo temporário na pasta de backup
    caminho_temp = os.path.join(BACKUP_DIR, arquivo.filename)
    with open(caminho_temp, "wb") as buffer:
        buffer.write(arquivo.file.read())

    # Substitui banco de dados atual pelo backup
    shutil.copy(caminho_temp, "sghss.db")

    # Registra log da restauração
    registrar_log(
        db,
        usuario_atual["email"],
        "Backup",
        acao="UPDATE",
        detalhes=f"Banco restaurado a partir de {arquivo.filename}"
    )

    return {"detail": "Banco de dados restaurado com sucesso"}
