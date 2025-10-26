from app.core import security  # Importa funções de segurança, como hash de senha
from app import models as m  # importa os modelos diretamente de app.models
from app.db import session  # importa o módulo de sessão do banco


def seed():
    db = session.get_db_session()  # Obtém uma instância de sessão do banco de dados

    # cria usuário admin se ausente
    if not db.query(m.Usuario).filter(m.Usuario.email == 'admin@vidaplus.test').first():
        # Cria usuário administrador padrão se não existir no banco
        admin = m.Usuario(
            email='admin@vidaplus.test',
            hashed_password=security.hash_password('adminpass'),  # Gera o hash da senha 'adminpass'
            papel='ADMIN'  # Define papel de administrador
        )
        db.add(admin)  # Adiciona o usuário à sessão para inserção

    # cria alguns pacientes
    if db.query(m.Paciente).count() == 0:
        # Se ainda não existem pacientes, adiciona dois registros de exemplo
        p1 = m.Paciente(nome='João da Silva')
        p2 = m.Paciente(nome='Maria Oliveira')
        db.add_all([p1, p2])  # Adiciona ambos à sessão

    db.commit()  # Confirma (salva) as alterações no banco de dados
    print('Seed concluído')  # Mensagem de conclusão no terminal


if __name__ == '__main__':
    seed()  # Executa a função "seed" diretamente ao rodar o script
