import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pytest
from app import create_app, db
from app.models import User, Post
from config import Config


class QAConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    ELASTICSEARCH_URL = None
    WTF_CSRF_ENABLED = False


@pytest.fixture
def app():
    app = create_app(QAConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def make_user(app):
    def _make(username='ana', email='ana@example.com', password='Clave123*'):
        u = User(username=username, email=email)
        u.set_password(password)
        db.session.add(u)
        db.session.commit()
        return u
    return _make


@pytest.fixture
def login(client):
    def _login(username='ana', password='Clave123*'):
        return client.post('/auth/login', data={'username': username, 'password': password},
                           follow_redirects=False)
    return _login


@pytest.fixture
def api_token(client, make_user):
    def _tok(username='ana', password='Clave123*'):
        import base64
        cred = base64.b64encode(f'{username}:{password}'.encode()).decode()
        r = client.post('/api/tokens', headers={'Authorization': f'Basic {cred}'})
        return r.get_json()['token']
    return _tok


# Selenium requiere navegador: se ejecuta aparte (ver qa/selenium)
collect_ignore = ['selenium', 'rendimiento', 'postman']
