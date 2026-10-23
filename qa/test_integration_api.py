"""Pruebas de INTEGRACION (API REST + BD). IDs IT-xx"""
import base64, json


def basic(u, p):
    return {'Authorization': 'Basic ' + base64.b64encode(f'{u}:{p}'.encode()).decode()}


def bearer(t):
    return {'Authorization': f'Bearer {t}'}


def test_IT01_crear_usuario_201(client):
    r = client.post('/api/users', json={'username': 'luis', 'email': 'luis@e.com', 'password': 'Clave123*'})
    assert r.status_code == 201
    assert r.get_json()['username'] == 'luis'
    assert '/api/users/' in r.headers['Location']


def test_IT02_crear_usuario_campos_faltantes_400(client):
    r = client.post('/api/users', json={'username': 'luis'})
    assert r.status_code == 400


def test_IT03_crear_usuario_duplicado_400(client, make_user):
    make_user()
    r = client.post('/api/users', json={'username': 'ana', 'email': 'otro@e.com', 'password': 'x'})
    assert r.status_code == 400


def test_IT04_token_con_credenciales_validas(client, make_user):
    make_user()
    r = client.post('/api/tokens', headers=basic('ana', 'Clave123*'))
    assert r.status_code == 200 and len(r.get_json()['token']) == 32


def test_IT05_token_con_credenciales_invalidas_401(client, make_user):
    make_user()
    assert client.post('/api/tokens', headers=basic('ana', 'mala')).status_code == 401


def test_IT06_listar_usuarios_sin_token_401(client):
    assert client.get('/api/users').status_code == 401


def test_IT07_listar_usuarios_con_token_200(client, make_user, api_token):
    make_user(); t = api_token()
    r = client.get('/api/users', headers=bearer(t))
    assert r.status_code == 200 and r.get_json()['_meta']['total_items'] == 1


def test_IT08_per_page_limitado_a_100(client, make_user, api_token):
    make_user(); t = api_token()
    r = client.get('/api/users?per_page=5000', headers=bearer(t))
    assert r.get_json()['_meta']['per_page'] == 100


def test_IT09_obtener_usuario_inexistente_404(client, make_user, api_token):
    make_user(); t = api_token()
    assert client.get('/api/users/999', headers=bearer(t)).status_code == 404


def test_IT10_actualizar_otro_usuario_403(client, make_user, api_token):
    make_user(); make_user('beto', 'b@e.com'); t = api_token()
    r = client.put('/api/users/2', json={'about_me': 'hack'}, headers=bearer(t))
    assert r.status_code == 403


def test_IT11_actualizar_propio_perfil_200(client, make_user, api_token):
    make_user(); t = api_token()
    r = client.put('/api/users/1', json={'about_me': 'hola'}, headers=bearer(t))
    assert r.status_code == 200 and r.get_json()['about_me'] == 'hola'


def test_IT12_revocar_token_y_reusar_401(client, make_user, api_token):
    make_user(); t = api_token()
    assert client.delete('/api/tokens', headers=bearer(t)).status_code == 204
    assert client.get('/api/users', headers=bearer(t)).status_code == 401


def test_IT13_seguidores_paginados(client, make_user, api_token):
    a = make_user(); b = make_user('beto', 'b@e.com')
    from app import db
    b.follow(a); db.session.commit()
    t = api_token()
    r = client.get('/api/users/1/followers', headers=bearer(t))
    assert r.get_json()['_meta']['total_items'] == 1


# ---- Pruebas negativas que revelan defectos (ver reporte) ----
def test_IT14_crear_usuario_email_invalido_deberia_400(client):
    r = client.post('/api/users', json={'username': 'x', 'email': 'esto-no-es-correo', 'password': 'abc'})
    assert r.status_code == 400, f'API acepto un email invalido (status {r.status_code})'


def test_IT15_crear_usuario_username_vacio_deberia_400(client):
    r = client.post('/api/users', json={'username': '', 'email': 'v@e.com', 'password': 'abc'})
    assert r.status_code == 400, f'API acepto username vacio (status {r.status_code})'


def test_IT16_crear_usuario_cuerpo_json_null_no_debe_dar_500(client):
    r = client.post('/api/users', data='null', content_type='application/json')
    assert r.status_code < 500, f'Error de servidor {r.status_code} con cuerpo null'


def test_IT17_crear_usuario_cuerpo_lista_no_debe_dar_500(client):
    r = client.post('/api/users', data='[]', content_type='application/json')
    assert r.status_code < 500, f'Error de servidor {r.status_code} con cuerpo lista'


def test_IT18_actualizar_con_about_me_mayor_140_deberia_400(client, make_user, api_token):
    make_user(); t = api_token()
    r = client.put('/api/users/1', json={'about_me': 'x' * 500}, headers=bearer(t))
    assert r.status_code == 400, f'API acepto about_me de 500 caracteres (status {r.status_code})'


def test_IT19_actualizar_username_vacio_deberia_400(client, make_user, api_token):
    make_user(); t = api_token()
    r = client.put('/api/users/1', json={'username': ''}, headers=bearer(t))
    assert r.status_code == 400, f'API acepto username vacio en PUT (status {r.status_code})'


def test_IT20_health_check_publico_y_con_bd(client):
    """Mejora evolutiva EV-01: endpoint de salud para monitoreo."""
    r = client.get('/api/health')
    assert r.status_code == 200
    body = r.get_json()
    assert body['status'] == 'ok' and body['database'] == 'ok'
