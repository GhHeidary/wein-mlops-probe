# Datei: tests/test_api.py – in VS Code einfügen und speichern
# Wir testen die Wein-API mit dem TestClient – ohne Server, direkt in Python.
# Braucht models/modell.joblib. In CI läuft der Test deshalb im Job "pipeline".

import json
from pathlib import Path

from fastapi.testclient import TestClient

from api.app import app

client = TestClient(app)
WEIN = json.loads(Path("beispiele/wein.json").read_text(encoding="utf-8"))


def test_health():
    antwort = client.get("/health")
    assert antwort.status_code == 200
    assert antwort.json() == {"status": "ok"}


def test_vorhersage_erster_wein():
    antwort = client.post("/vorhersage", json=WEIN)
    assert antwort.status_code == 200
    assert antwort.json() == {"klasse": 0, "name": "Sorte 1", "wahrscheinlichkeit": 0.97}


def test_nullen_werden_abgelehnt():
    nullen = {name: 0 for name in WEIN}
    antwort = client.post("/vorhersage", json=nullen)
    assert antwort.status_code == 422


def test_unbekannte_klasse():
    antwort = client.get("/klassen/7")
    assert antwort.status_code == 404


def test_batch():
    antwort = client.post("/vorhersage/batch", json=[WEIN, WEIN])
    assert antwort.status_code == 200
    assert len(antwort.json()) == 2


def test_batch_leer():
    antwort = client.post("/vorhersage/batch", json=[])
    assert antwort.status_code == 400