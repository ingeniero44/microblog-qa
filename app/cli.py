import os
import re
import subprocess
from flask import Blueprint
import click

bp = Blueprint('cli', __name__, cli_group=None)


@bp.cli.group()
def translate():
    """Translation and localization commands."""
    pass


@translate.command()
@click.argument('lang')
def init(lang):
    """Initialize a new language."""
    if not re.fullmatch(r'[A-Za-z_]{2,10}', lang):
        raise click.BadParameter('invalid language code')
    if subprocess.run(['pybabel', 'extract', '-F', 'babel.cfg', '-k', '_l',
                       '-o', 'messages.pot', '.']).returncode:
        raise RuntimeError('extract command failed')
    if subprocess.run(['pybabel', 'init', '-i', 'messages.pot',
                       '-d', 'app/translations', '-l', lang]).returncode:
        raise RuntimeError('init command failed')
    os.remove('messages.pot')


@translate.command()
def update():
    """Update all languages."""
    if subprocess.run(['pybabel', 'extract', '-F', 'babel.cfg', '-k', '_l',
                       '-o', 'messages.pot', '.']).returncode:
        raise RuntimeError('extract command failed')
    if subprocess.run(['pybabel', 'update', '-i', 'messages.pot',
                       '-d', 'app/translations']).returncode:
        raise RuntimeError('update command failed')
    os.remove('messages.pot')


@translate.command()
def compile():
    """Compile all languages."""
    if subprocess.run(['pybabel', 'compile', '-d', 'app/translations']).returncode:
        raise RuntimeError('compile command failed')
