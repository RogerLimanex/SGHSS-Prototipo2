# Fornece engine e sessão para o banco (SQLite por padrão)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite:///./sghss.db"  # ajuste se for outro banco

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}  # apenas para SQLite
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# Função utilitária para fornecer sessão do DB
def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
