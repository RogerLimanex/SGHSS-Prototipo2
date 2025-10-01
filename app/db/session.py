from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Caminho do banco SQLite
DATABASE_URL = "sqlite:///./sghss.db"

# Criar engine
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

# Criar session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base do SQLAlchemy
Base = declarative_base()


# Dependência para FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
