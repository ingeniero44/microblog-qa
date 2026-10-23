import time
import sqlalchemy as sa
from flask import g, request, current_app
from flask_httpauth import HTTPBasicAuth, HTTPTokenAuth
from app import db
from app.models import User
from app.api.errors import error_response

basic_auth = HTTPBasicAuth()
token_auth = HTTPTokenAuth()


MAX_FAILED_ATTEMPTS = 5
LOCK_WINDOW_SECONDS = 60


def _attempts(key):
    store = current_app.__dict__.setdefault('_login_failures', {})
    now = time.time()
    store[key] = [t for t in store.get(key, []) if now - t < LOCK_WINDOW_SECONDS]
    return store[key]


@basic_auth.verify_password
def verify_password(username, password):
    key = (request.remote_addr, username)
    if len(_attempts(key)) >= MAX_FAILED_ATTEMPTS:
        g.rate_limited = True
        return None
    user = db.session.scalar(sa.select(User).where(User.username == username))
    if user and user.check_password(password):
        _attempts(key).clear()
        return user
    _attempts(key).append(time.time())


@basic_auth.error_handler
def basic_auth_error(status):
    if g.get('rate_limited'):
        return error_response(429, 'too many failed attempts, try again later')
    return error_response(status)


@token_auth.verify_token
def verify_token(token):
    return User.check_token(token) if token else None


@token_auth.error_handler
def token_auth_error(status):
    return error_response(status)
