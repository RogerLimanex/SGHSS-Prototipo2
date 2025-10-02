from app.db.session import Base, engine
from app import models


def criar_tabelas():
    """Cria todas as tabelas do banco de dados"""
    Base.metadata.create_all(bind=engine)


def popular_dados(db=None):
    """Popula dados iniciais, como usuário admin"""
    from sqlalchemy.orm import Session
    from app.models import Usuario

    session = db or Session(bind=engine)
    if not session.query(Usuario).filter(Usuario.email == "admin@example.com").first():
        admin = Usuario(email="admin@example.com", hashed_password="admin123", papel="ADMIN")
        session.add(admin)
        session.commit()
