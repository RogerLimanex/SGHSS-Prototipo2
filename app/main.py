from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles  # ✅ para servir arquivos da pasta uploads
from contextlib import asynccontextmanager
import os

# Importação dos roteadores existentes
from app.api.v1.autenticacao import roteador as roteador_autenticacao
from app.api.v1.pacientes import roteador as roteador_pacientes
from app.api.v1.medicos import roteador as roteador_medicos
from app.api.v1.consultas import roteador as roteador_consultas
from app.api.v1.prescricoes import roteador as roteador_prescricoes
from app.api.v1.teleconsultas import roteador as roteador_teleconsultas
from app.api.v1.prontuario import roteador as roteador_prontuario
from app.api.v1.auditoria import roteador as roteador_auditoria

# ✅ Novos módulos
from app.api.v1.financeiro import roteador as roteador_financeiro
from app.api.v1.relatorios import roteador as roteador_relatorios
from app.api.v1.backup import roteador as roteador_backup

# Banco de dados
from app.db.migrations import criar_tabelas, popular_dados


# ----------------------------
# Ciclo de vida da aplicação
# ----------------------------
@asynccontextmanager
async def ciclo_vida(app: FastAPI):
    print("🔧 Iniciando migrações...")

    db_path = "./sghss.db"
    print(f"📁 Caminho do banco: {os.path.abspath(db_path)}")
    print(f"📁 Existe: {os.path.exists(db_path)}")

    if os.path.exists(db_path):
        size = os.path.getsize(db_path)
        print(f"📁 Tamanho do arquivo: {size} bytes")

    try:
        criar_tabelas()
        popular_dados()
    except Exception as e:
        print(f"❌ ERRO nas migrações: {e}")
        import traceback
        traceback.print_exc()
        raise

    yield


# ----------------------------
# Instanciação da aplicação
# ----------------------------
app = FastAPI(title="SGHSS - Protótipo", lifespan=ciclo_vida)

# ----------------------------
# Servir arquivos estáticos
# ----------------------------
UPLOAD_DIR = os.path.join("app", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# ----------------------------
# Registro de Roteadores
# ----------------------------
app.include_router(roteador_autenticacao, prefix="/api/v1/autenticacao", tags=["Autenticação"])
app.include_router(roteador_pacientes, prefix="/api/v1/pacientes", tags=["Pacientes"])
app.include_router(roteador_medicos, prefix="/api/v1/medicos", tags=["Médicos"])
app.include_router(roteador_consultas, prefix="/api/v1/consultas", tags=["Consultas"])
app.include_router(roteador_teleconsultas, prefix="/api/v1/teleconsultas", tags=["Teleconsultas"])
app.include_router(roteador_prescricoes, prefix="/api/v1/prescricoes", tags=["Prescrições"])
app.include_router(roteador_prontuario, prefix="/api/v1/prontuario", tags=["Prontuários"])
app.include_router(roteador_financeiro, prefix="/api/v1/financeiro", tags=["Financeiro"])
app.include_router(roteador_relatorios, prefix="/api/v1/relatorios", tags=["Relatórios"])
app.include_router(roteador_auditoria, prefix="/api/v1/auditoria", tags=["Auditoria"])
app.include_router(roteador_backup, prefix="/api/v1/backup", tags=["Backup e Restauração"])


# ----------------------------
# Rota raiz
# ----------------------------
@app.get("/")
def ler_raiz():
    return {
        "message": "Bem-vindo à API SGHSS",
        "versao": "1.0",
        "status": "online",
        "documentacao": "/docs"
    }
