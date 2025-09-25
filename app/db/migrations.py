from app.db import engine, Base
from app.models import Patient, User


def create_tables():
    """Cria todas as tabelas"""
    print("🔄 Criando tabelas...")

    # DEBUG: Verificar se os modelos estão registrados
    print("📋 Modelos carregados:")
    for table_name, table in Base.metadata.tables.items():
        print(f"   - {table_name}: {table}")

    # DEBUG: Verificar se engine está conectado
    print(f"🔧 Engine: {engine}")
    print(f"🔧 URL: {engine.url}")

    # Criar tabelas
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ create_all() executado")
    except Exception as e:
        print(f"❌ Erro no create_all: {e}")
        raise

    # Verificar tabelas criadas
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"📊 Tabelas no banco: {tables}")


def seed_data():
    from app.db import SessionLocal
    from app.models import User
    from app.core.security import hash_password

    print("🌱 Iniciando seed...")

    # Verificar tabelas primeiro
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"📊 Tabelas antes do seed: {tables}")

    if 'users' not in tables:
        print("❌ Tabela 'users' não encontrada! Seed abortado.")
        return

    db = SessionLocal()
    try:
        # Verificar se usuário já existe
        existing = db.query(User).filter(User.email == 'admin@vidaplus.com').first()
        if existing:
            print("ℹ️ Usuário admin já existe")
        else:
            admin_user = User(
                email='admin@vidaplus.com',
                hashed_password=hash_password('adminpass'),
                role='ADMIN'
            )
            db.add(admin_user)
            db.commit()
            print("✅ Usuário admin criado!")
    except Exception as e:
        print(f"❌ Erro no seed: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()
