# D:\ProjectSGHSS\app\db\session.py
# Fornece engine e sessão para o banco (SQLite por padrão)

from sqlalchemy import create_engine  # Criação da engine de conexão
from sqlalchemy.orm import sessionmaker, declarative_base  # Para sessões e modelos

# Caminho do banco de dados SQLite (pode ser alterado para outro DB)
DATABASE_URL = "sqlite:///./sghss.db"

# Cria a engine de conexão
# check_same_thread=False → necessário no SQLite quando usado em múltiplas threads (FastAPI)
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # Apenas para SQLite
)

# Cria a fábrica de sessões
# autocommit=False → commits manuais
# autoflush=False → evita flush automático antes de query
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base declarativa para os modelos SQLAlchemy
Base = declarative_base()


# ------------------------------------------------------------
# Função utilitária para fornecer sessão do DB
# ------------------------------------------------------------
def get_db_session():
    """
    Cria e fornece uma sessão do banco de dados.
    Usa 'yield' para fechar a sessão automaticamente após uso.
    """
    db = SessionLocal()
    try:
        yield db  # Fornece a sessão
    finally:
        db.close()  # Garante fechamento da sessão após uso
