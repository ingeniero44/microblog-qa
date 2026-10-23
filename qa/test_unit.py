"""Pruebas de UNIDAD (modelos). IDs UT-xx"""
import pytest
from datetime import datetime, timezone, timedelta
from app import db
from app.models import User, Post


def test_UT01_password_hash_no_es_texto_plano(make_user):
    u = make_user(password='secreta')
    assert u.password_hash != 'secreta'
    assert u.check_password('secreta')


def test_UT02_password_incorrecta_rechazada(make_user):
    u = make_user(password='secreta')
    assert not u.check_password('otra')


def test_UT03_avatar_usa_email_en_minusculas(app):
    a = User(username='a', email='JUAN@Example.com')
    b = User(username='b', email='juan@example.com')
    assert a.avatar(64) == b.avatar(64)


def test_UT04_avatar_incluye_tamano(app):
    u = User(username='a', email='a@e.com')
    assert u.avatar(200).endswith('s=200')


def test_UT05_follow_y_unfollow(make_user):
    u1 = make_user('u1', 'u1@e.com'); u2 = make_user('u2', 'u2@e.com')
    u1.follow(u2); db.session.commit()
    assert u1.is_following(u2) and u2.followers_count() == 1
    u1.unfollow(u2); db.session.commit()
    assert not u1.is_following(u2) and u2.followers_count() == 0


def test_UT06_follow_duplicado_no_duplica(make_user):
    u1 = make_user('u1', 'u1@e.com'); u2 = make_user('u2', 'u2@e.com')
    u1.follow(u2); u1.follow(u2); db.session.commit()
    assert u1.following_count() == 1


def test_UT07_following_posts_orden_y_contenido(make_user):
    u1 = make_user('u1', 'u1@e.com'); u2 = make_user('u2', 'u2@e.com'); u3 = make_user('u3', 'u3@e.com')
    now = datetime.now(timezone.utc)
    p1 = Post(body='p1', author=u1, timestamp=now + timedelta(seconds=1))
    p2 = Post(body='p2', author=u2, timestamp=now + timedelta(seconds=4))
    p3 = Post(body='p3', author=u3, timestamp=now + timedelta(seconds=3))
    db.session.add_all([p1, p2, p3]); db.session.commit()
    u1.follow(u2); db.session.commit()
    assert [p.body for p in db.session.scalars(u1.following_posts())] == ['p2', 'p1']


def test_UT08_token_reset_valido(make_user):
    u = make_user()
    t = u.get_reset_password_token()
    assert User.verify_reset_password_token(t) == u


def test_UT09_token_reset_expirado(make_user):
    u = make_user()
    t = u.get_reset_password_token(expires_in=-1)
    assert User.verify_reset_password_token(t) is None


def test_UT10_token_reset_manipulado(make_user):
    make_user()
    assert User.verify_reset_password_token('abc.def.ghi') is None


def test_UT11_token_api_se_reutiliza_si_vigente(make_user):
    u = make_user()
    t1 = u.get_token(); db.session.commit()
    t2 = u.get_token()
    assert t1 == t2


def test_UT12_revocar_token_invalida_acceso(make_user):
    u = make_user()
    t = u.get_token(); db.session.commit()
    u.revoke_token(); db.session.commit()
    assert User.check_token(t) is None


def test_UT13_to_dict_no_expone_email_por_defecto(make_user):
    u = make_user()
    from flask import current_app
    with current_app.test_request_context():
        assert 'email' not in u.to_dict()
        assert u.to_dict(include_email=True)['email'] == u.email


@pytest.mark.parametrize('n,ok', [(0, True), (139, True), (140, True)])
def test_UT14_post_longitud_limite_modelo(make_user, n, ok):
    u = make_user()
    p = Post(body='x' * n, author=u)
    db.session.add(p); db.session.commit()
    assert p.id is not None


def test_UT15_cli_rechaza_codigo_de_idioma_malicioso(app):
    """Regresion BUG-10: el comando 'translate init' no debe ejecutar comandos de shell."""
    runner = app.test_cli_runner()
    r = runner.invoke(args=['translate', 'init', 'es; touch /tmp/pwned'])
    assert r.exit_code != 0
    import os
    assert not os.path.exists('/tmp/pwned')
