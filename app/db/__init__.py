# D:\ProjectSGHSS\app\db\__init__.py
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

# Caminho do banco SQLite
DATABASE_URL = "sqlite:///./sghss.db"

# Criação da engine com:
# - check_same_thread=False → permite uso em múltiplas threads (necessário no FastAPI)
# - timeout=30 → espera até 30 segundos se o banco estiver bloqueado
engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False,
        "timeout": 30
    }
)

# Ativa o modo WAL (Write-Ahead Logging)
# Esse modo permite múltiplas conexões simultâneas com menos bloqueios
with engine.connect() as conn:
    conn.execute(text("PRAGMA journal_mode=WAL;"))

# Criação da sessão padrão
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para os modelos do SQLAlchemy
Base = declarative_base()


# Dependência para injetar sessão no FastAPI
def get_db():
    """Cria e fecha a sessão do banco automaticamente a cada requisição."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
