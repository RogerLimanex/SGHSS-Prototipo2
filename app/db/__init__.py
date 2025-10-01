from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from .session import Base, engine, get_db_session

DATABASE_URL = "sqlite:///./sghss.db"  # ou outra URL do seu banco
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Dependency para FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
