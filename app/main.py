from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api.v1 import auth, patients
from app.db import models, session
from scripts import seed

app = FastAPI(title='SGHSS - Protótipo')

app.mount('/frontend', StaticFiles(directory='frontend'), name='frontend')

app.include_router(auth.router, prefix='/api/v1/auth', tags=['auth'])
app.include_router(patients.router, prefix='/api/v1/pacientes', tags=['pacientes'])

@app.on_event('startup')
def startup():
    models.Base.metadata.create_all(bind=session.engine)
    try:
        seed.seed()
    except Exception as e:
        print('seed error', e)
