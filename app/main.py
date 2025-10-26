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

from fastapi import FastAPI  # Importa o framework principal para criação da API
from fastapi.staticfiles import StaticFiles  # Permite servir arquivos estáticos (imagens, PDFs, etc.)
from contextlib import asynccontextmanager  # Gerencia o ciclo de vida assíncrono da aplicação
import os  # Biblioteca padrão para manipulação de caminhos e arquivos

# ----------------------------
# Importação dos roteadores da API
# ----------------------------
from app.api.v1.autenticacao import roteador as roteador_autenticacao  # Roteador de autenticação
from app.api.v1.pacientes import roteador as roteador_pacientes  # Roteador para pacientes
from app.api.v1.medicos import roteador as roteador_medicos  # Roteador para médicos
from app.api.v1.consultas import roteador as roteador_consultas  # Roteador de consultas
from app.api.v1.prescricoes import roteador as roteador_prescricoes  # Roteador de prescrições médicas
from app.api.v1.teleconsultas import roteador as roteador_teleconsultas  # Roteador de teleconsultas
from app.api.v1.prontuario import roteador as roteador_prontuario  # Roteador de prontuários médicos
from app.api.v1.leito import roteador as roteador_leito  # Roteador de gerenciamento de leitos
from app.api.v1.suprimento import roteador as roteador_suprimento  # Roteador para controle de suprimentos
from app.api.v1.auditoria import roteador as roteador_auditoria  # Roteador de auditoria do sistema
from app.api.v1.financeiro import roteador as roteador_financeiro  # Roteador do módulo financeiro
from app.api.v1.relatorios import roteador as roteador_relatorios  # Roteador de relatórios e estatísticas
from app.api.v1.backup import roteador as roteador_backup  # Roteador de backup do sistema

# Banco de dados e migrações
from app.db.migrations import criar_tabelas, popular_dados  # Funções para criação e inicialização do banco


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
    print("🔧 Iniciando migrações...")  # Log de início das migrações

    db_path = "./sghss.db"  # Caminho do arquivo do banco de dados
    print(f"📁 Caminho do banco: {os.path.abspath(db_path)}")  # Mostra o caminho absoluto
    print(f"📁 Existe: {os.path.exists(db_path)}")  # Verifica se o banco já existe

    if os.path.exists(db_path):  # Se o arquivo de banco existir
        size = os.path.getsize(db_path)  # Obtém o tamanho do arquivo
        print(f"📦 Tamanho do arquivo: {size} bytes")  # Exibe o tamanho

    try:
        criar_tabelas()  # Cria as tabelas do banco, se não existirem
        popular_dados()  # Insere dados iniciais (ex: usuário admin)
    except Exception as e:  # Caso haja erro na migração
        print(f"❌ ERRO nas migrações: {e}")  # Exibe o erro
        import traceback  # Importa para exibir rastreamento detalhado
        traceback.print_exc()  # Mostra o stack trace completo
        raise  # Relança a exceção para interromper a inicialização

    yield  # Pausa e permite a execução da aplicação após as migrações


# ----------------------------
# Instanciação da aplicação FastAPI
# ----------------------------
app = FastAPI(
    title="SGHSS - Protótipo",  # Nome exibido na documentação
    description="🩺 API do Sistema de Gestão Hospitalar e Saúde Simplificada (SGHSS)",  # Descrição
    version="1.0",  # Versão da API
    lifespan=ciclo_vida  # Vincula o ciclo de vida assíncrono
)

# ----------------------------
# Configuração de arquivos estáticos
# ----------------------------
UPLOAD_DIR = os.path.join("app", "uploads")  # Define o diretório de uploads
os.makedirs(UPLOAD_DIR, exist_ok=True)  # Cria o diretório se não existir
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")  # Monta o diretório como rota pública

# ----------------------------
# Registro de Roteadores (Endpoints da API)
# ----------------------------
app.include_router(roteador_autenticacao, prefix="/api/v1/autenticacao", tags=["Autenticação"])  # Autenticação
app.include_router(roteador_pacientes, prefix="/api/v1/pacientes", tags=["Pacientes"])  # Pacientes
app.include_router(roteador_medicos, prefix="/api/v1/medicos", tags=["Médicos"])  # Médicos
app.include_router(roteador_consultas, prefix="/api/v1/consultas", tags=["Consultas"])  # Consultas médicas
app.include_router(roteador_teleconsultas, prefix="/api/v1/teleconsultas", tags=["Teleconsultas"])  # Teleconsultas
app.include_router(roteador_prescricoes, prefix="/api/v1/prescricoes", tags=["Prescrições"])  # Prescrições
app.include_router(roteador_prontuario, prefix="/api/v1/prontuario", tags=["Prontuários"])  # Prontuário do paciente
app.include_router(roteador_leito, prefix="/api/v1/leito", tags=["Leitos"])  # Leitos hospitalares
app.include_router(roteador_suprimento, prefix="/api/v1/suprimento", tags=["Suprimentos"])  # Suprimentos hospitalares
app.include_router(roteador_financeiro, prefix="/api/v1/financeiro", tags=["Financeiro"])  # Controle financeiro
app.include_router(roteador_relatorios, prefix="/api/v1/relatorios", tags=["Relatórios"])  # Relatórios do sistema
app.include_router(roteador_auditoria, prefix="/api/v1/auditoria", tags=["Auditoria"])  # Auditoria do sistema
app.include_router(roteador_backup, prefix="/api/v1/backup")  # Backup e restauração de dados


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
        "message": "Bem-vindo à API SGHSS",  # Mensagem de boas-vindas
        "versao": "1.0",  # Versão da API
        "status": "online",  # Status atual da API
        "documentacao": "/docs"  # Link para a documentação interativa do FastAPI
    }
