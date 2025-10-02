from app.db import session, models as m
from app.core import security


def seed():
    db = session.get_db_session()
    # cria usuário admin se ausente
    if not db.query(m.Usuario).filter(m.Usuario.email == 'admin@vidaplus.test').first():
        admin = m.Usuario(email='admin@vidaplus.test', hashed_password=security.hash_password('adminpass'),
                          papel='ADMIN')
        db.add(admin)
    # cria alguns pacientes
    if db.query(m.Paciente).count() == 0:
        p1 = m.Paciente(nome='João da Silva')
        p2 = m.Paciente(nome='Maria Oliveira')
        db.add_all([p1, p2])
    db.commit()
    print('Seed concluído')


if __name__ == '__main__':
    seed()
