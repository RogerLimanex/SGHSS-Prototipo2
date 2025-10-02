from fastapi import FastAPI
from contextlib import asynccontextmanager
import os
from app.db import Base, engine  # necessário para criar as tabelas
from app.api.v1.auth import roteador as roteador_auth
from app.api.v1.pacientes import roteador as roteador_pacientes
from app.api.v1.medicos import roteador as roteador_medicos
from app.api.v1.consultas import roteador as roteador_consultas
from app.api.v1.prescricoes import roteador as roteador_prescricoes
from app.api.v1.teleconsultas import roteador as roteador_teleconsultas
from app.db.migrations import popular_dados


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
        # Cria todas as tabelas definidas nos modelos
        Base.metadata.create_all(bind=engine)
        print("✅ Todas as tabelas foram criadas (se ainda não existiam)")

        # Popula dados iniciais (usuário admin, etc.)
        popular_dados()
        print("✅ Dados iniciais populados com sucesso!")
    except Exception as e:
        print(f"❌ ERRO nas migrações: {e}")
        import traceback
        traceback.print_exc()
        raise

    yield


# ←←← Aplicação FastAPI
app = FastAPI(title="SGHSS - Protótipo", lifespan=ciclo_vida)

# Inclui os roteadores traduzidos
app.include_router(roteador_auth, prefix="/api/v1/auth", tags=["Autenticação"])
app.include_router(roteador_pacientes, prefix="/api/v1/patients", tags=["Pacientes"])
app.include_router(roteador_medicos, prefix="/api/v1/doctors", tags=["Médicos"])
app.include_router(roteador_consultas, prefix="/api/v1/appointments", tags=["Consultas"])
app.include_router(roteador_prescricoes, prefix="/api/v1/prescriptions", tags=["Prescrições"])
app.include_router(roteador_teleconsultas, prefix="/api/v1/teleconsultations", tags=["Teleconsultas"])



@app.get("/")
def ler_raiz():
    # Rota raiz com mensagem de boas-vindas
    return {"message": "Bem-vindo à API SGHSS"}
