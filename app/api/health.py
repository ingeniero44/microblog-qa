import sqlalchemy as sa
from app import db
from app.api import bp


@bp.route('/health', methods=['GET'])
def health():
    """Verificacion de salud para monitoreo / balanceadores (EV-01)."""
    try:
        db.session.execute(sa.text('SELECT 1'))
        return {'status': 'ok', 'database': 'ok'}
    except Exception:
        return {'status': 'degraded', 'database': 'error'}, 503
