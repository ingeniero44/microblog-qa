"""Pruebas de RENDIMIENTO (Locust). Escenarios PF-01..PF-04"""
import re
import itertools
_cuentas = itertools.count(0)
from locust import HttpUser, task, between


class UsuarioWeb(HttpUser):
    weight = 3
    wait_time = between(0.5, 1.5)

    def on_start(self):
        r = self.client.get('/auth/login', name='PF-01 GET /auth/login')
        token = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', r.text).group(1)
        n = (next(_cuentas) % 20) + 1
        self.client.post('/auth/login', data={'csrf_token': token, 'username': f'user{n}',
                                              'password': 'Clave123*'}, name='PF-01 POST /auth/login')

    @task(5)
    def explorar(self):
        self.client.get('/explore', name='PF-02 GET /explore')

    @task(3)
    def inicio(self):
        self.client.get('/index', name='PF-02 GET /index')

    @task(2)
    def perfil(self):
        self.client.get('/user/user1', name='PF-02 GET /user/<u>')


class UsuarioApi(HttpUser):
    weight = 2
    wait_time = between(0.2, 1.0)

    def on_start(self):
        n = 21 + (next(_cuentas) % 20)
        r = self.client.post('/api/tokens', auth=(f'user{n}', 'Clave123*'), name='PF-03 POST /api/tokens')
        self.h = {'Authorization': 'Bearer ' + r.json()['token']} if r.status_code == 200 else {}

    @task(4)
    def listar(self):
        self.client.get('/api/users?per_page=50', headers=self.h, name='PF-04 GET /api/users')

    @task(1)
    def usuario(self):
        self.client.get('/api/users/1', headers=self.h, name='PF-04 GET /api/users/<id>')
