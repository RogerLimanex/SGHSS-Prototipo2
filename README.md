# SGHSS - Protótipo (FastAPI + Frontend)

Este repositório contém um protótipo mínimo do SGHSS (Sistema de Gestão Hospitalar e de Serviços de Saúde).
Inclui um backend em FastAPI (SQLite para desenvolvimento) e um frontend simples (HTML/CSS).

# Como rodar localmente (modo simples)
Recomendado: Python 3.11+

```bash
python -m venv .venv
source .venv/bin/activate   # ou .venv\Scripts\activate no Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Abra no navegador: http://localhost:8000/frontend/login.html

# Usando Docker (opcional)
Construir e subir com docker-compose:
```bash
docker-compose up --build
```

# Observações
- Esta é uma versão protótipo para testes e aprendizado. Em produção, use PostgreSQL, variáveis de ambiente seguras, TLS, KMS para chaves e configuração de usuários/senhas.
- JWT secret padrão está em `app/core/security.py` como `CHANGE_ME`. Troque para valor seguro em produção.
