import os
from contextlib import asynccontextmanager
from fastapi import FastAPI

# Importa os roteadores traduzidos
from app.api.v1.auth import roteador as roteador_auth
from app.api.v1.pacientes import roteador as roteador_pacientes
from app.api.v1.medicos import roteador as roteador_medicos
from app.api.v1.consultas import roteador as roteador_consultas
from app.api.v1.medical import roteador as roteador_medical  # este arquivo já tinha funcionalidades médicas
from app.db.migrations import criar_tabelas, popular_dados


@asynccontextmanager
async def ciclo_vida(_app: FastAPI):
    # Mensagens de inicialização / migração
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
        print("✅ Migrações concluídas com sucesso!")
    except Exception as e:
        print(f"❌ ERRO nas migrações: {e}")
        import traceback
        traceback.print_exc()
        raise

    yield


# ←←← Aplicação FastAPI
app = FastAPI(title="SGHSS - Protótipo", lifespan=ciclo_vida)

# Inclui os roteadores traduzidos com os mesmos prefixes originais
app.include_router(roteador_auth, prefix="/api/v1/auth", tags=["auth"])
app.include_router(roteador_pacientes, prefix="/api/v1/patients", tags=["patients"])
app.include_router(roteador_medicos, prefix="/api/v1/doctors", tags=["doctors"])
app.include_router(roteador_consultas, prefix="/api/v1/appointments", tags=["appointments"])
app.include_router(roteador_medical, prefix="/api/v1/medical", tags=["medical"])  # manter tag para compatibilidade


@app.get("/")
def ler_raiz():
    # Rota raiz com mensagem de boas-vindas
    return {"message": "Bem-vindo à API SGHSS"}
