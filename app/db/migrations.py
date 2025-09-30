# app/db/migrations.py
from app.db import Base, engine, SessionLocal
from app.models import User, Patient, Doctor
from app.core.security import hash_password
from sqlalchemy.exc import SQLAlchemyError


def create_tables():
    """Cria todas as tabelas no banco"""
    print("🔄 Criando tabelas...")
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Tabelas criadas com sucesso")
    except SQLAlchemyError as e:
        print(f"❌ Erro ao criar tabelas: {e}")
        raise


def seed_data():
    """Insere dados iniciais (admin)"""
    db = SessionLocal()
    try:
        # Verifica se usuário admin já existe
        admin_email = 'admin@vidaplus.com'
        existing = db.query(User).filter(User.email == admin_email).first()
        if existing:
            print("ℹ️ Usuário admin já existe")
        else:
            admin_user = User(
                email=admin_email,
                hashed_password=hash_password('adminpass'),
                role='ADMIN'
            )
            db.add(admin_user)
            db.commit()
            print("✅ Usuário admin criado")
    except SQLAlchemyError as e:
        print(f"❌ Erro no seed: {e}")
        db.rollback()
    finally:
        db.close()
