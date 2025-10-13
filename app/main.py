"""
📘 **Módulo Principal da Aplicação SGHSS**

Este módulo inicializa a aplicação FastAPI, configura o ciclo de vida,
monta os diretórios estáticos, registra os roteadores (módulos de API)
e executa as migrações de banco de dados no início da aplicação.

🧩 Estrutura:
- Inicialização da aplicação FastAPI.
- Configuração dos diretórios de upload.
- Registro de todos os endpoints da API.
- Execução automática de migrações na inicialização.
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

# ----------------------------
# Importação dos roteadores da API
# ----------------------------
from app.api.v1.autenticacao import roteador as roteador_autenticacao
from app.api.v1.pacientes import roteador as roteador_pacientes
from app.api.v1.medicos import roteador as roteador_medicos
from app.api.v1.consultas import roteador as roteador_consultas
from app.api.v1.prescricoes import roteador as roteador_prescricoes
from app.api.v1.teleconsultas import roteador as roteador_teleconsultas
from app.api.v1.prontuario import roteador as roteador_prontuario
from app.api.v1.leito import roteador as roteador_leito
from app.api.v1.suprimento import roteador as roteador_suprimento
from app.api.v1.auditoria import roteador as roteador_auditoria
from app.api.v1.financeiro import roteador as roteador_financeiro
from app.api.v1.relatorios import roteador as roteador_relatorios
from app.api.v1.backup import roteador as roteador_backup

# Banco de dados e migrações
from app.db.migrations import criar_tabelas, popular_dados


# ----------------------------
# Ciclo de vida da aplicação
# ----------------------------
@asynccontextmanager
async def ciclo_vida(app: FastAPI):
    """
    🔄 **Ciclo de Vida da Aplicação**

    Executado no momento em que a API é iniciada.
    Realiza verificações no banco de dados e aplica as migrações
    automaticamente antes de aceitar requisições.
    """
    print("🔧 Iniciando migrações...")

    db_path = "./sghss.db"
    print(f"📁 Caminho do banco: {os.path.abspath(db_path)}")
    print(f"📁 Existe: {os.path.exists(db_path)}")

    if os.path.exists(db_path):
        size = os.path.getsize(db_path)
        print(f"📦 Tamanho do arquivo: {size} bytes")

    try:
        criar_tabelas()  # Cria tabelas se não existirem
        popular_dados()  # Popula dados iniciais (usuários padrão, etc.)
    except Exception as e:
        print(f"❌ ERRO nas migrações: {e}")
        import traceback
        traceback.print_exc()
        raise

    yield


# ----------------------------
# Instanciação da aplicação FastAPI
# ----------------------------
app = FastAPI(
    title="SGHSS - Protótipo",
    description="🩺 API do Sistema de Gestão Hospitalar e Saúde Simplificada (SGHSS)",
    version="1.0",
    lifespan=ciclo_vida
)

# ----------------------------
# Configuração de arquivos estáticos
# ----------------------------
UPLOAD_DIR = os.path.join("app", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)  # Garante que o diretório exista
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# ----------------------------
# Registro de Roteadores (Endpoints da API)
# ----------------------------
app.include_router(roteador_autenticacao, prefix="/api/v1/autenticacao", tags=["Autenticação"])
app.include_router(roteador_pacientes, prefix="/api/v1/pacientes", tags=["Pacientes"])
app.include_router(roteador_medicos, prefix="/api/v1/medicos", tags=["Médicos"])
app.include_router(roteador_consultas, prefix="/api/v1/consultas", tags=["Consultas"])
app.include_router(roteador_teleconsultas, prefix="/api/v1/teleconsultas", tags=["Teleconsultas"])
app.include_router(roteador_prescricoes, prefix="/api/v1/prescricoes", tags=["Prescrições"])
app.include_router(roteador_prontuario, prefix="/api/v1/prontuario", tags=["Prontuários"])
app.include_router(roteador_leito, prefix="/api/v1/leito", tags=["Leitos"])
app.include_router(roteador_suprimento, prefix="/api/v1/suprimento", tags=["Suprimentos"])
app.include_router(roteador_financeiro, prefix="/api/v1/financeiro", tags=["Financeiro"])
app.include_router(roteador_relatorios, prefix="/api/v1/relatorios", tags=["Relatórios"])
app.include_router(roteador_auditoria, prefix="/api/v1/auditoria", tags=["Auditoria"])
app.include_router(roteador_backup, prefix="/api/v1/backup")  # Sem parâmetro `tags=[]` para evitar duplicações


# ----------------------------
# Rota raiz da aplicação
# ----------------------------
@app.get("/", summary="Página inicial da API")
def ler_raiz():
    """
    🌐 **Endpoint Raiz da API SGHSS**

    Retorna informações básicas sobre o status da aplicação,
    versão atual e link da documentação interativa.

    **Exemplo de resposta:**
    ```json
    {
        "message": "Bem-vindo à API SGHSS",
        "versao": "1.0",
        "status": "online",
        "documentacao": "/docs"
    }
    ```
    """
    return {
        "message": "Bem-vindo à API SGHSS",
        "versao": "1.0",
        "status": "online",
        "documentacao": "/docs"
    }
