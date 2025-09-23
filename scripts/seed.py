from app.db import session, models as m
from app.core import security

def seed():
    db = session.get_db_session()
    # create admin user if missing
    if not db.query(m.User).filter(m.User.email=='admin@vidaplus.test').first():
        admin = m.User(email='admin@vidaplus.test', hashed_password=security.hash_password('adminpass'), role='ADMIN')
        db.add(admin)
    # create some patients
    if db.query(m.Patient).count() == 0:
        p1 = m.Patient(nome='João da Silva')
        p2 = m.Patient(nome='Maria Oliveira')
        db.add_all([p1,p2])
    db.commit()
    print('Seed concluído')

if __name__ == '__main__':
    seed()
