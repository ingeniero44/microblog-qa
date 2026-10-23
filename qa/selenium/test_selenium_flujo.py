"""Pruebas de SISTEMA con Selenium WebDriver (ST-S01..ST-S03).
NO fueron ejecutadas por el asistente (el entorno no tiene navegador). Ejecutalas en tu equipo:
    pip install selenium pytest
    (en otra terminal) flask run --port 5000      # con la app corriendo y BD vacia
    pytest qa/selenium -v
Selenium 4.6+ descarga el driver automaticamente (Selenium Manager)."""
import uuid
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE = 'http://127.0.0.1:5000'


@pytest.fixture
def driver():
    opts = webdriver.ChromeOptions()
    opts.add_argument('--window-size=1400,1000')
    opts.add_argument('--lang=en-US')
    opts.add_experimental_option('prefs', {'intl.accept_languages': 'en-US,en'})
    d = webdriver.Chrome(options=opts)
    d.implicitly_wait(3)
    yield d
    d.quit()


def registrar_y_entrar(d, usuario, clave='Clave123*'):
    d.get(f'{BASE}/auth/register')
    d.find_element(By.ID, 'username').send_keys(usuario)
    d.find_element(By.ID, 'email').send_keys(f'{usuario}@example.com')
    d.find_element(By.ID, 'password').send_keys(clave)
    d.find_element(By.ID, 'password2').send_keys(clave)
    d.find_element(By.ID, 'submit').click()
    d.find_element(By.ID, 'username').send_keys(usuario)
    d.find_element(By.ID, 'password').send_keys(clave)
    d.find_element(By.ID, 'submit').click()


def test_ST_S01_registro_login_y_publicacion(driver):
    registrar_y_entrar(driver, 'sel_' + uuid.uuid4().hex[:6])
    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, 'post')))
    driver.find_element(By.ID, 'post').send_keys('Hola desde Selenium')
    driver.find_element(By.ID, 'submit').click()
    WebDriverWait(driver, 10).until(lambda d: 'Hola desde Selenium' in d.page_source)
    driver.save_screenshot('evidencia_ST_S01.png')


def test_ST_S02_login_invalido(driver):
    driver.get(f'{BASE}/auth/login')
    driver.find_element(By.ID, 'username').send_keys('noexiste')
    driver.find_element(By.ID, 'password').send_keys('mala')
    driver.find_element(By.ID, 'submit').click()
    WebDriverWait(driver, 10).until(lambda d: 'Invalid username or password' in d.page_source)


def test_ST_S03_ruta_privada_redirige(driver):
    driver.get(f'{BASE}/explore')
    assert '/auth/login' in driver.current_url
