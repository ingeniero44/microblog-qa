import sqlalchemy as sa
from flask import request, url_for, abort
from app import db
from app.models import User
from app.api import bp
from app.api.auth import token_auth
from app.api.errors import bad_request
from email_validator import validate_email, EmailNotValidError

MIN_PASSWORD_LENGTH = 8


def validate_user_payload(data, partial=False):
    """Devuelve un mensaje de error (str) o None si el cuerpo JSON es valido."""
    if not isinstance(data, dict):
        return 'request body must be a JSON object'
    if 'username' in data:
        u = data['username']
        if not isinstance(u, str) or not u.strip() or len(u) > 64:
            return 'username must be a non-empty string of at most 64 characters'
    if 'email' in data:
        e = data['email']
        if not isinstance(e, str) or len(e) > 120:
            return 'email must be a valid address of at most 120 characters'
        try:
            validate_email(e, check_deliverability=False)
        except EmailNotValidError:
            return 'email must be a valid address'
    if 'about_me' in data and data['about_me'] is not None:
        if not isinstance(data['about_me'], str) or len(data['about_me']) > 140:
            return 'about_me must be a string of at most 140 characters'
    if 'password' in data:
        pw = data['password']
        if not isinstance(pw, str) or len(pw) < MIN_PASSWORD_LENGTH:
            return f'password must have at least {MIN_PASSWORD_LENGTH} characters'
    return None


@bp.route('/users/<int:id>', methods=['GET'])
@token_auth.login_required
def get_user(id):
    return db.get_or_404(User, id).to_dict()


@bp.route('/users', methods=['GET'])
@token_auth.login_required
def get_users():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    return User.to_collection_dict(sa.select(User), page, per_page,
                                   'api.get_users')


@bp.route('/users/<int:id>/followers', methods=['GET'])
@token_auth.login_required
def get_followers(id):
    user = db.get_or_404(User, id)
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    return User.to_collection_dict(user.followers.select(), page, per_page,
                                   'api.get_followers', id=id)


@bp.route('/users/<int:id>/following', methods=['GET'])
@token_auth.login_required
def get_following(id):
    user = db.get_or_404(User, id)
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    return User.to_collection_dict(user.following.select(), page, per_page,
                                   'api.get_following', id=id)


@bp.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    error = validate_user_payload(data)
    if error:
        return bad_request(error)
    if 'username' not in data or 'email' not in data or 'password' not in data:
        return bad_request('must include username, email and password fields')
    if db.session.scalar(sa.select(User).where(
            User.username == data['username'])):
        return bad_request('please use a different username')
    if db.session.scalar(sa.select(User).where(
            User.email == data['email'])):
        return bad_request('please use a different email address')
    user = User()
    user.from_dict(data, new_user=True)
    db.session.add(user)
    db.session.commit()
    return user.to_dict(), 201, {'Location': url_for('api.get_user',
                                                     id=user.id)}


@bp.route('/users/<int:id>', methods=['PUT'])
@token_auth.login_required
def update_user(id):
    if token_auth.current_user().id != id:
        abort(403)
    user = db.get_or_404(User, id)
    data = request.get_json()
    error = validate_user_payload(data, partial=True)
    if error:
        return bad_request(error)
    if 'username' in data and data['username'] != user.username and \
        db.session.scalar(sa.select(User).where(
            User.username == data['username'])):
        return bad_request('please use a different username')
    if 'email' in data and data['email'] != user.email and \
        db.session.scalar(sa.select(User).where(
            User.email == data['email'])):
        return bad_request('please use a different email address')
    user.from_dict(data, new_user=False)
    db.session.commit()
    return user.to_dict()
