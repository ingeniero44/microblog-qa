import sys, os
sys.path.insert(0, os.getcwd())
from app import create_app, db
from app.models import User, Post
app = create_app()
with app.app_context():
    db.drop_all(); db.create_all()
    users = []
    for i in range(1, 41):
        u = User(username=f'user{i}', email=f'user{i}@example.com'); u.set_password('Clave123*'); users.append(u)
    db.session.add_all(users); db.session.commit()
    for i in range(400):
        db.session.add(Post(body=f'Publicacion de prueba numero {i}', author=users[i % 40]))
    db.session.commit()
    for u in users[1:]:
        users[0].follow(u); u.follow(users[0])
    db.session.commit()
    print('seed ok', db.session.query(User).count(), db.session.query(Post).count())
