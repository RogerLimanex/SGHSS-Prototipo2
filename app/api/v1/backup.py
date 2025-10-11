# D:\ProjectSGHSS\app\api\v1\backup.py
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

roteador = APIRouter()

BACKUP_DIR = "backups"
os.makedirs(BACKUP_DIR, exist_ok=True)


def obter_usuario_atual(current_user=Depends(security.get_current_user), db: Session = Depends(get_db)):
    usuario_email = current_user.get("email")
    if not usuario_email:
        usuario = db.query(m.Usuario).filter(m.Usuario.id == int(current_user.get("id"))).first()
        if usuario:
            usuario_email = usuario.email
            current_user["email"] = usuario.email
    return current_user


# ----------------------------
# Gerar backup do banco
# ----------------------------
@roteador.get("/backup/exportar")
def gerar_backup(
        db: Session = Depends(get_db),
        usuario_atual=Depends(obter_usuario_atual)
):
    if usuario_atual["papel"] != "ADMIN":
        raise HTTPException(status_code=403, detail="Acesso negado: apenas ADMIN")

    nome_arquivo = f"sghss_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    caminho_destino = os.path.join(BACKUP_DIR, nome_arquivo)

    shutil.copy("sghss.db", caminho_destino)

    registrar_log(db, usuario_atual["email"], "Backup", acao="CREATE",
                  detalhes=f"Backup gerado: {nome_arquivo}")

    return FileResponse(caminho_destino, filename=nome_arquivo, media_type="application/octet-stream")


# ----------------------------
# Restaurar banco a partir de backup
# ----------------------------
@roteador.post("/backup/importar")
def restaurar_backup(
        arquivo: UploadFile = File(...),
        db: Session = Depends(get_db),
        usuario_atual=Depends(obter_usuario_atual)
):
    if usuario_atual["papel"] != "ADMIN":
        raise HTTPException(status_code=403, detail="Acesso negado: apenas ADMIN")

    if not arquivo.filename.endswith(".db"):
        raise HTTPException(status_code=400, detail="Arquivo inválido. Envie um .db")

    caminho_temp = os.path.join(BACKUP_DIR, arquivo.filename)
    with open(caminho_temp, "wb") as buffer:
        buffer.write(arquivo.file.read())

    shutil.copy(caminho_temp, "sghss.db")

    registrar_log(db, usuario_atual["email"], "Backup", acao="UPDATE",
                  detalhes=f"Banco restaurado a partir de {arquivo.filename}")

    return {"detail": "Banco de dados restaurado com sucesso"}
