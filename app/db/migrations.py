# D:\ProjectSGHSS\app\db\migrations.py
from datetime import datetime
from app.db.session import Base, engine, SessionLocal
from app.models import Usuario, Medico, Paciente, StatusConsulta, AuditLog
from app.core import security


def criar_tabelas():
    """
    Cria todas as tabelas do banco caso não existam.
    Inclui as tabelas de auditoria e entidades principais.
    """
    Base.metadata.create_all(bind=engine)
    print("✅ Todas as tabelas foram criadas (se ainda não existiam)")


def popular_dados():
    """
    Insere registros iniciais no banco, caso ainda não existam.
    Cria o usuário admin e alguns registros de teste.
    """
    with SessionLocal() as session:
        try:
            # Usuário admin
            if not session.query(Usuario).filter(Usuario.email == "admin@teste.com").first():
                admin = Usuario(
                    email="admin@teste.com",
                    hashed_password=security.hash_password("123456"),
                    papel="ADMIN",
                    ativo=True,
                    criado_em=datetime.now()
                )
                session.add(admin)

            # Médicos de teste
            if not session.query(Medico).filter(Medico.nome == "Dr. João Silva").first():
                session.add(Medico(nome="Dr. João Silva", crm="123456"))
            if not session.query(Medico).filter(Medico.nome == "Dra. Maria Souza").first():
                session.add(Medico(nome="Dra. Maria Souza", crm="654321"))

            # Pacientes de teste
            if not session.query(Paciente).filter(Paciente.nome == "Carlos Alberto").first():
                session.add(Paciente(nome="Carlos Alberto", data_nascimento=datetime(1990, 5, 10)))
            if not session.query(Paciente).filter(Paciente.nome == "Ana Paula").first():
                session.add(Paciente(nome="Ana Paula", data_nascimento=datetime(1985, 8, 22)))

            session.commit()
            print("✅ Dados iniciais populados com sucesso!")
        except Exception as e:
            session.rollback()
            print(f"❌ Erro ao popular dados: {e}")
            import traceback
            traceback.print_exc()
