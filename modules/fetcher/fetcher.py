import json
import os
import subprocess

DB_PATH      = os.path.join(os.path.dirname(__file__), 'database.sqlite')
JSON_PATH    = os.path.join(os.path.dirname(__file__), 'japji_full.json')
FETCH_SCRIPT = os.path.join(os.path.dirname(__file__), 'fetch_japji.js')


def _ensure_json():
    """Re-generate japji_full.json from the SQLite DB if stale or missing."""
    if not os.path.exists(JSON_PATH) or (
        os.path.getmtime(DB_PATH) > os.path.getmtime(JSON_PATH)
    ):
        subprocess.run(['node', FETCH_SCRIPT], check=True)


def load_japji() -> list[dict]:
    """
    Returns list of pauris:
      [{ pauri: int, shabad_id: str, lines: [{ type: str, text: str }] }]
    """
    _ensure_json()
    with open(JSON_PATH, encoding='utf-8') as f:
        return json.load(f)
