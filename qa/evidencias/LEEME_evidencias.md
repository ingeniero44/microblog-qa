# Evidencias generadas por ejecucion real (octubre 2026)
Proyecto: Microblog (Flask), https://github.com/miguelgrinberg/microblog, commit base a975ef6, licencia MIT.
- 01_antes/: ejecucion ANTES de corregir (68 pruebas: 58 pasan, 10 fallan; cobertura 76 %).
- 02_despues/: ejecucion FINAL tras las correcciones (74 pruebas, todas pasan), con cobertura HTML.
- 03_analisis_estatico/: bandit, flake8, radon y pip-audit.
- 04_rendimiento/: Locust antes/despues (30 usuarios, 45 s, Gunicorn 2 workers, SQLite).
- 05_postman/: Newman, 11 peticiones y 19 aserciones.
- 06_parches_git/: commits y diff de las correcciones.
No ejecutado en este entorno: Selenium (sin navegador). Script listo en qa/selenium.
