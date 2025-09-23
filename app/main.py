from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api.v1 import auth, patients
# from app.db import models, session
# from scripts import seed
import warnings
from contextlib import asynccontextmanager

# Suprimir warnings do passlib sem import desnecessário
warnings.filterwarnings("ignore",
                        message=".*bcrypt version.*",
                        category=UserWarning)

app = FastAPI(title='SGHSS - Protótipo')

app.mount('/frontend', StaticFiles(directory='frontend'), name='frontend')

app.include_router(auth.router, prefix='/api/v1/auth', tags=['auth'])
app.include_router(patients.router, prefix='/api/v1/pacientes', tags=['pacientes'])


@asynccontextmanager
async def lifespan(_app: FastAPI):
    print("Seed concluído")
    yield


app = FastAPI(title='SGHSS - Protótipo', lifespan=lifespan)

# Include routers - ESTAS LINHAS SÃO ESSENCIAIS!
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(patients.router, prefix="/api/v1/patients", tags=["patients"])


@app.get("/")
def read_root():
    return {"message": "Bem-vindo à API SGHSS"}

# @app.on_event('startup')
# def startup():
#     models.Base.metadata.create_all(bind=session.engine)
#     try:
#         seed.seed()
#     except Exception as e:
#         print('seed error', e)
