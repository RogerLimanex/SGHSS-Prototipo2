from sqlalchemy import create_engine, text  # Engine do SQLAlchemy e execução de comandos SQL
from sqlalchemy.orm import sessionmaker, declarative_base  # Sessão ORM e base declarativa para modelos

# Caminho do banco SQLite local
DATABASE_URL = "sqlite:///./sghss.db"

# Criação da engine SQLAlchemy
# - check_same_thread=False → permite uso do mesmo banco em múltiplas threads (necessário no FastAPI)
# - timeout=30 → espera até 30 segundos se o banco estiver bloqueado
engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False,
        "timeout": 30
    }
)

# Ativa o modo WAL (Write-Ahead Logging) do SQLite
# Permite múltiplas conexões simultâneas com menos bloqueios
with engine.connect() as conn:
    conn.execute(text("PRAGMA journal_mode=WAL;"))

# Criação da sessão padrão para manipulação de dados
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base declarativa para criação dos modelos ORM
Base = declarative_base()


# Dependência FastAPI para injetar sessão automaticamente
def get_db():
    """Cria e fecha a sessão do banco automaticamente a cada requisição."""
    db = SessionLocal()
    try:
        yield db  # Fornece a sessão ao endpoint
    finally:
        db.close()  # Fecha a sessão ao final da requisição
