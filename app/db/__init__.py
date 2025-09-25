from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# URL do banco - DEVE SER A MESMA em todos os lugares
SQLALCHEMY_DATABASE_URL = "sqlite:///./sghss.db"

# Engine ÚNICA para toda a aplicação
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# SessionMaker ÚNICO
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base ÚNICA
Base = declarative_base()


def get_db_session():
    """Função para obter sessão do banco - DEVE SER USADA POR TODOS"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
