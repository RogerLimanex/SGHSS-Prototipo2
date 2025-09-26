import os
from contextlib import asynccontextmanager
from fastapi import FastAPI

# Importe os routers
from app.api.v1.auth import router as auth_router
from app.api.v1.patients import router as patients_router
from app.api.v1.doctors import router as doctors_router
from app.db.migrations import create_tables, seed_data


@asynccontextmanager
async def lifespan(_app: FastAPI):
    print("🔧 Iniciando migrações...")

    # DEBUG: Verificar se o arquivo do banco existe
    db_path = "./sghss.db"  # ← Corrigi para sghss.db (era sighs.db)
    print(f"📁 Caminho do banco: {os.path.abspath(db_path)}")
    print(f"📁 Existe: {os.path.exists(db_path)}")

    # DEBUG: Verificar tamanho do arquivo
    if os.path.exists(db_path):
        size = os.path.getsize(db_path)
        print(f"📁 Tamanho do arquivo: {size} bytes")

    # Executar migrações
    try:
        create_tables()
        seed_data()
        print("✅ Migrações concluídas com sucesso!")
    except Exception as e:
        print(f"❌ ERRO nas migrações: {e}")
        import traceback
        traceback.print_exc()
        raise

    yield


# ←←← APENAS UMA DEFINIÇÃO DA APP ↓↓↓
app = FastAPI(title='SGHSS - Protótipo', lifespan=lifespan)

# Include routers - TODOS os routers aqui
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(patients_router, prefix="/api/v1/patients", tags=["patients"])
app.include_router(doctors_router, prefix="/api/v1/doctors", tags=["doctors"])  # ← ESTAVA FALTANDO


@app.get("/")
def read_root():
    return {"message": "Bem-vindo à API SGHSS"}
