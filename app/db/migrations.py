from app.db.session import Base, engine
from app import models


def create_tables():
    """Cria todas as tabelas do banco de dados"""
    Base.metadata.create_all(bind=engine)


def seed_data(db=None):
    """Popula dados iniciais, como usuário admin"""
    from sqlalchemy.orm import Session
    from app.models import User

    session = db or Session(bind=engine)
    if not session.query(User).filter(User.email == "admin@example.com").first():
        admin = User(email="admin@example.com", hashed_password="admin123", role="ADMIN")
        session.add(admin)
        session.commit()
