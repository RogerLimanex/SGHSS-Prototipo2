from datetime import datetime  # Para datas de criação e nascimento
from app.db.session import Base, engine, SessionLocal  # Base declarativa, engine e sessão
from app.models import Usuario, Medico, Paciente, StatusConsulta, AuditLog, Financeiro  # Modelos principais
from app.core import security  # Para hash de senha


# ============================================================
# Função: criar todas as tabelas do banco
# ============================================================
def criar_tabelas():
    """
    Cria todas as tabelas do banco caso não existam.
    Inclui entidades principais, auditoria e financeiro.
    """
    Base.metadata.create_all(bind=engine)  # Criação física das tabelas
    print("✅ Todas as tabelas foram criadas (se ainda não existiam)")


# ============================================================
# Função: popular dados iniciais
# ============================================================
def popular_dados():
    """
    Insere registros iniciais no banco se ainda não existirem.
    - Usuário ADMIN
    - Médicos de teste
    - Pacientes de teste
    """
    with SessionLocal() as session:  # Contexto de sessão do SQLAlchemy
        try:
            # Usuário admin
            if not session.query(Usuario).filter(Usuario.email == "admin@teste.com").first():
                admin = Usuario(
                    email="admin@teste.com",
                    hashed_password=security.hash_password("123456"),  # Senha padrão com hash
                    papel="ADMIN",  # Papel de administrador
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

            # Confirma alterações no banco
            session.commit()
            print("✅ Dados iniciais populados com sucesso!")
        except Exception as e:
            session.rollback()  # Desfaz alterações em caso de erro
            print(f"❌ Erro ao popular dados: {e}")
            import traceback
            traceback.print_exc()  # Exibe stack trace para depuração
