"""Pruebas de SEGURIDAD (OWASP Top 10). IDs SEC-xx"""
import base64
import jwt, time
import sqlalchemy as sa
from app import db
from app.models import User


def test_SEC01_inyeccion_sql_en_login_no_autentica(client, make_user):
    make_user()
    r = client.post('/auth/login', data={'username': "' OR '1'='1' --", 'password': 'x'}, follow_redirects=False)
    assert client.get('/index').status_code == 302  # sigue sin sesion


def test_SEC02_inyeccion_sql_en_url_de_usuario(client, make_user, login):
    make_user(); login()
    r = client.get("/user/ana' OR '1'='1")
    assert r.status_code == 404


def test_SEC03_xss_en_about_me_escapado(client, make_user, login):
    make_user(); login()
    client.post('/edit_profile', data={'username': 'ana', 'about_me': '<img src=x onerror=alert(1)>'})
    r = client.get('/user/ana')
    assert b'<img src=x onerror=alert(1)>' not in r.data


def test_SEC04_contrasenas_con_hash_salado(make_user):
    a = make_user('a', 'a@e.com', 'misma'); b = make_user('b', 'b@e.com', 'misma')
    assert a.password_hash != b.password_hash
    assert a.password_hash.startswith(('scrypt:', 'pbkdf2:'))


def test_SEC05_rutas_privadas_requieren_sesion(client):
    for ruta in ['/index', '/explore', '/user/ana', '/edit_profile', '/messages', '/export_posts']:
        assert client.get(ruta).status_code in (302, 401, 404, 405), ruta
        assert client.get(ruta).status_code != 200, ruta


def test_SEC06_csrf_activo_por_defecto():
    from app import create_app
    from config import Config
    class C(Config):
        TESTING = True
        SQLALCHEMY_DATABASE_URI = 'sqlite://'
        ELASTICSEARCH_URL = None
    app = create_app(C)
    with app.app_context():
        db.create_all()
        u = User(username='ana', email='a@e.com'); u.set_password('x'); db.session.add(u); db.session.commit()
        c = app.test_client()
        r = c.post('/auth/login', data={'username': 'ana', 'password': 'x'})
        assert r.status_code == 200 and b'CSRF' in r.data  # rechazado por falta de token


def test_SEC07_open_redirect_con_next_netloc_bloqueado(client, make_user):
    make_user()
    r = client.post('/auth/login?next=//evil.com', data={'username': 'ana', 'password': 'Clave123*'})
    assert 'evil.com' not in r.headers['Location']


def test_SEC08_open_redirect_con_barra_invertida(client, make_user):
    make_user()
    r = client.post('/auth/login?next=/\\evil.com', data={'username': 'ana', 'password': 'Clave123*'})
    from urllib.parse import urlsplit
    loc = r.headers['Location']
    assert urlsplit(loc).netloc == '' and not loc.startswith('//'), f'Redireccion a destino externo: {loc}'


def test_SEC09_secret_key_por_defecto_no_deberia_usarse():
    from config import Config
    assert Config.SECRET_KEY != 'you-will-never-guess', 'SECRET_KEY por defecto publica en el repositorio'


def test_SEC10_token_de_reset_falsificable_con_clave_por_defecto(client, make_user):
    u = make_user()
    from config import Config
    forged = jwt.encode({'reset_password': u.id, 'exp': time.time() + 600}, 'you-will-never-guess', algorithm='HS256')
    r = client.post(f'/auth/reset_password/{forged}', data={'password': 'hack', 'password2': 'hack'})
    db.session.expire_all()
    assert not db.session.get(User, u.id).check_password('hack'), 'Se pudo restablecer la contrasena con un token falsificado'


def test_SEC11_fuerza_bruta_api_sin_bloqueo(client, make_user):
    make_user()
    cred = lambda p: {'Authorization': 'Basic ' + base64.b64encode(f'ana:{p}'.encode()).decode()}
    codes = [client.post('/api/tokens', headers=cred(f'intento{i}')).status_code for i in range(50)]
    assert 429 in codes, 'Sin limite de intentos: 50 intentos fallidos seguidos sin bloqueo (no hay 429)'


def test_SEC12_politica_de_contrasena_minima(client):
    r = client.post('/api/users', json={'username': 'u', 'email': 'u@e.com', 'password': '1'})
    assert r.status_code == 400, 'La API acepta contrasenas de 1 caracter'


def test_SEC13_cabeceras_de_seguridad_http(client, make_user, login):
    make_user(); login()
    h = client.get('/index').headers
    faltan = [x for x in ['X-Content-Type-Options', 'X-Frame-Options', 'Content-Security-Policy'] if x not in h]
    assert not faltan, f'Cabeceras ausentes: {faltan}'


def test_SEC14_enumeracion_de_usuarios_en_reset(client, make_user):
    make_user()
    r1 = client.post('/auth/reset_password_request', data={'email': 'ana@example.com'}, follow_redirects=True)
    r2 = client.post('/auth/reset_password_request', data={'email': 'noexiste@example.com'}, follow_redirects=True)
    assert (b'Check your email' in r1.data) == (b'Check your email' in r2.data)
