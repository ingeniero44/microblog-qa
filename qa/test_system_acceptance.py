"""Pruebas de SISTEMA (flujos web completos) y ACEPTACION (Dado/Cuando/Entonces). IDs ST-xx / AT-xx"""
from app import db
from app.models import User, Post
import sqlalchemy as sa


def registrar(client, u='ana', e='ana@example.com', p='Clave123*', p2=None):
    return client.post('/auth/register', data={'username': u, 'email': e, 'password': p,
                                                'password2': p2 or p}, follow_redirects=True)


def test_ST01_flujo_registro_login_publicar(client):
    r = registrar(client)
    assert b'you are now a registered user' in r.data
    r = client.post('/auth/login', data={'username': 'ana', 'password': 'Clave123*'}, follow_redirects=True)
    assert b'Hi, ana' in r.data or b'ana' in r.data
    r = client.post('/', data={'post': 'Mi primer post'}, follow_redirects=True)
    assert b'Your post is now live' in r.data and b'Mi primer post' in r.data


def test_ST02_pagina_privada_redirige_a_login(client):
    r = client.get('/index')
    assert r.status_code == 302 and '/auth/login' in r.headers['Location']


def test_ST03_login_invalido_muestra_error(client, make_user):
    make_user()
    r = client.post('/auth/login', data={'username': 'ana', 'password': 'mala'}, follow_redirects=True)
    assert b'Invalid username or password' in r.data


def test_ST04_registro_passwords_distintas_rechazado(client):
    r = registrar(client, p2='otra')
    assert db.session.scalar(sa.select(User).where(User.username == 'ana')) is None


def test_ST05_registro_email_invalido_rechazado(client):
    registrar(client, e='no-es-email')
    assert db.session.scalar(sa.select(User).where(User.username == 'ana')) is None


def test_ST06_post_vacio_rechazado(client, make_user, login):
    make_user(); login()
    client.post('/', data={'post': ''}, follow_redirects=True)
    assert db.session.scalar(sa.select(sa.func.count()).select_from(Post)) == 0


def test_ST07_post_mayor_140_rechazado(client, make_user, login):
    make_user(); login()
    client.post('/', data={'post': 'x' * 141}, follow_redirects=True)
    assert db.session.scalar(sa.select(sa.func.count()).select_from(Post)) == 0


def test_ST08_seguir_y_dejar_de_seguir(client, make_user, login):
    make_user(); make_user('beto', 'b@e.com'); login()
    client.post('/follow/beto', follow_redirects=True)
    a = db.session.scalar(sa.select(User).where(User.username == 'ana'))
    b = db.session.scalar(sa.select(User).where(User.username == 'beto'))
    assert a.is_following(b)
    client.post('/unfollow/beto', follow_redirects=True)
    assert not a.is_following(b)


def test_ST09_no_puede_seguirse_a_si_mismo(client, make_user, login):
    make_user(); login()
    r = client.post('/follow/ana', follow_redirects=True)
    assert b'cannot follow yourself' in r.data


def test_ST10_editar_perfil(client, make_user, login):
    make_user(); login()
    client.post('/edit_profile', data={'username': 'ana', 'about_me': 'Estudiante'}, follow_redirects=True)
    assert db.session.scalar(sa.select(User).where(User.username == 'ana')).about_me == 'Estudiante'


def test_ST11_nombre_usuario_duplicado_en_edicion(client, make_user, login):
    make_user(); make_user('beto', 'b@e.com'); login()
    r = client.post('/edit_profile', data={'username': 'beto', 'about_me': ''}, follow_redirects=True)
    assert b'Please use a different username' in r.data


def test_ST12_explorar_muestra_posts_de_todos(client, make_user, login):
    u2 = make_user('beto', 'b@e.com'); make_user(); 
    db.session.add(Post(body='post de beto', author=u2)); db.session.commit()
    login()
    assert b'post de beto' in client.get('/explore').data


def test_ST13_logout_cierra_sesion(client, make_user, login):
    make_user(); login()
    client.get('/auth/logout')
    assert client.get('/index').status_code == 302


def test_ST14_usuario_inexistente_404(client, make_user, login):
    make_user(); login()
    assert client.get('/user/fantasma').status_code == 404


def test_ST15_xss_en_post_es_escapado(client, make_user, login):
    make_user(); login()
    client.post('/', data={'post': '<script>alert(1)</script>'}, follow_redirects=True)
    r = client.get('/explore')
    assert b'<script>alert(1)</script>' not in r.data


# ---------- ACEPTACION (criterios Dado/Cuando/Entonces) ----------
def test_AT01_un_usuario_nuevo_puede_registrarse_e_ingresar(client):
    # Dado un visitante sin cuenta; Cuando se registra y entra; Entonces ve su pagina de inicio
    registrar(client)
    r = client.post('/auth/login', data={'username': 'ana', 'password': 'Clave123*'}, follow_redirects=True)
    assert r.status_code == 200 and b'Home' in r.data


def test_AT02_el_inicio_muestra_solo_posts_propios_y_de_seguidos(client, make_user, login):
    ana = make_user(); beto = make_user('beto', 'b@e.com'); carla = make_user('carla', 'c@e.com')
    db.session.add_all([Post(body='de-beto', author=beto), Post(body='de-carla', author=carla)])
    ana.follow(beto); db.session.commit(); login()
    r = client.get('/index')
    assert b'de-beto' in r.data and b'de-carla' not in r.data


def test_AT03_la_paginacion_limita_a_25_posts(client, make_user, login):
    ana = make_user()
    for i in range(30):
        db.session.add(Post(body=f'p{i}', author=ana))
    db.session.commit(); login()
    r = client.get('/index')
    assert r.data.count(b'class="post') <= 25 or r.data.count(b'<table') <= 26
    assert b'Older posts' in r.data


def test_AT04_el_idioma_es_se_aplica_con_accept_language(tmp_path):
    # Se usa una app aislada sin contexto global para que el idioma no quede en cache
    from app import create_app
    from config import Config

    class C(Config):
        TESTING = True
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{tmp_path}/t.db"
        ELASTICSEARCH_URL = None
        WTF_CSRF_ENABLED = False
    app = create_app(C)
    with app.app_context():
        db.create_all()
        u = User(username='ana', email='a@e.com'); u.set_password('x')
        db.session.add(u); db.session.commit()
    c = app.test_client()
    c.post('/auth/login', data={'username': 'ana', 'password': 'x'}, headers={'Accept-Language': 'es'})
    r = c.get('/index', headers={'Accept-Language': 'es'})
    assert 'Inicio' in r.data.decode()
