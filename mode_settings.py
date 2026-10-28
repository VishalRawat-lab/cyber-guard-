"""Shared mode selection for the desktop and web frontends."""
import json
import os
from pathlib import Path

SETTINGS_FILE = Path(__file__).with_name('mode_settings.json')


def current_mode():
    try:
        mode = json.loads(SETTINGS_FILE.read_text(encoding='utf-8')).get('mode')
        if mode in ('demo', 'oracle'):
            return mode
    except (OSError, ValueError, TypeError):
        pass
    return 'oracle' if os.getenv('TRACKER_DEMO', '1').lower() in ('0', 'false', 'no') else 'demo'


def make_database(mode=None):
    from database import Database
    return Database(username=os.getenv('ORACLE_USER', 'INCIDENT_USER'),
                    password=os.getenv('ORACLE_PASSWORD', ''),
                    dsn=os.getenv('ORACLE_DSN', 'localhost:1521/freepdb1'),
                    demo_mode=(mode or current_mode()) == 'demo')


def switch_mode(mode):
    """Verify Oracle connectivity before saving a switch. Never save passwords."""
    if mode not in ('demo', 'oracle'):
        raise ValueError('Choose Demo or Oracle.')
    if mode == 'oracle':
        if not os.getenv('ORACLE_PASSWORD'):
            raise RuntimeError('Set ORACLE_PASSWORD in the terminal before choosing Oracle mode.')
        db = make_database('oracle')
        try:
            db.connect()
            # Verify that the incident table is accessible, not just that login succeeds.
            db.fetch_incidents()
        finally:
            db.close()
    SETTINGS_FILE.write_text(json.dumps({'mode': mode}, indent=2), encoding='utf-8')
