# wein-mlops

![CI](https://github.com/DEIN_NAME/wein-mlops/actions/workflows/ci.yml/badge.svg)

Kursprojekt im Modul MLOps (IfaDW): Klassifikation von Weinen mit dem
Wine-Datensatz aus scikit-learn.

## Umgebung

    conda env create -f environment.yml
    conda activate mlops-kurs

## MLflow-Server starten (ab Tag 7)

    docker compose up -d --build
    export MLFLOW_TRACKING_URI=http://localhost:5000

Die MLflow UI läuft unter http://localhost:5000.

## Training

    python src/train.py

## Model Registry (ab Tag 8)

Bestes Modell registrieren und Champion wählen:

    python src/registrieren.py

Champion laden und testen:

    python src/modell_laden.py

Champion als API starten (Port 5001):

    mlflow models serve -m "models:/wein-klassifikator@champion" -p 5001 --env-manager local

API testen:

    curl -sS -X POST http://localhost:5001/invocations -H "Content-Type: application/json" -d @anfrage.json

Rollback auf eine ältere Version (danach die API neu starten):

    python src/alias_setzen.py <version>

## Daten und Pipeline mit DVC (ab Tag 9)

Daten vom DVC-Remote holen (nach einem neuen Klon):

    dvc pull

Pipeline ausführen (validieren, vorbereiten, trainieren, bewerten):

    dvc repro
    dvc metrics show

Parameter stehen in `params.yaml`. Nach einer Änderung:

    dvc repro
    dvc params diff
    dvc metrics diff

Neue Datenversion speichern:

    dvc add data/raw/wein.csv
    git add data/raw/wein.csv.dvc
    git commit -m "Neue Datenversion"
    dvc push

## Tests und CI (ab Tag 10)

Tests lokal ausführen:

    pytest -v

GitHub Actions (Datei `.github/workflows/ci.yml`, ab Tag 11 erweitert):

- startet bei jedem Push und Pull Request auf `main`, von Hand und jeden Montag um 06:17 Uhr
- Job `tests`: Tests mit Python 3.12, 3.13 und 3.14 (Matrix), Pakete aus dem Cache
- Job `datenpruefung`: erst nach grünen Tests; erzeugt `data/raw/wein.csv` und validiert sie
- Artefakt `validierungsbericht` (`reports/validierung.json`), 7 Tage zum Download

Ergebnis: Tab **Actions** auf GitHub. Den geplanten Lauf abschalten:
**Actions** → **CI** → **⋯** → **Disable workflow**.

## Orchestrierung und Experimente (ab Tag 12)

Prüfen, was neu laufen würde (ohne etwas zu starten):

    dvc status
    dvc repro --dry

Experimente ohne Commit (`--temp`: der Arbeitsordner bleibt unverändert):

    dvc exp run --temp -n baeume-50 -S trainieren.n_estimators=50
    dvc exp show --only-changed --md | cat
    dvc exp apply baeume-50

Workflow `.github/workflows/pipeline.yml`:

- startet von Hand (**Run workflow**) und jeden Montag um 06:47 Uhr
- erzeugt die Rohdaten, führt `dvc repro --force` aus
- prüft die Reproduzierbarkeit (`dvc.lock` und `metrics.json` unverändert)
- schreibt die Metriken in die Zusammenfassung des Runs

Optional: Ist `MLFLOW_TRACKING_URI` gesetzt, speichert `bewerten.py` jeden Lauf
im MLflow-Experiment `wein-pipeline`.


## End-to-End-Automatisierung (ab Tag 13)

Bei jedem Push und Pull Request auf `main` (Workflow `ci.yml`):

1. Job `tests`: Tests mit Python 3.12, 3.13 und 3.14
2. Job `pipeline` (erst wenn alle Tests grün sind):
   Rohdaten erzeugen, `dvc repro --force`, Reproduzierbarkeit prüfen,
   **Quality Gate**, Modell als Artefakt `modell` (7 Tage)

Quality Gate lokal prüfen:

    python src/quality_gate.py

Die Mindestwerte stehen in `params.yaml` unter `quality_gate`.


## Modell-API und Batch-Vorhersage (ab Tag 14)

Beide nutzen das Modell der Pipeline: `models/modell.joblib`.

Batch-Vorhersage (viele Weine aus einer CSV-Datei):

    python src/batch_vorhersage.py beispiele/neue_weine.csv

Das Ergebnis steht in `ausgabe/vorhersagen.csv` (nicht in Git).

API starten (im Projektordner):

    uvicorn api.app:app --reload

Dokumentation im Browser: http://127.0.0.1:8000/docs

| Methode | Pfad | Ergebnis |
|---|---|---|
| GET | `/health` | `{"status": "ok"}` |
| GET | `/modell` | Parameter und Metriken des Modells |
| GET | `/klassen/{nummer}` | Name einer Klasse |
| GET | `/beispiele?anzahl=2` | Beispielweine |
| POST | `/vorhersage` | Klasse und Wahrscheinlichkeit für einen Wein |

Beispiel:

    curl -X POST http://127.0.0.1:8000/vorhersage \
         -H "Content-Type: application/json" \
         -d @beispiele/wein.json


## API-Version 0.2.0 und API-Tests (ab Tag 15)

Die API prüft jetzt die Eingaben:

- Jeder Messwert muss in einem erlaubten Bereich liegen (Grenzen aus den Trainingsdaten). Sonst: `422`.
- Unbekannte Klasse bei `/klassen/{nummer}`: `404`.
- Leere Liste bei `/vorhersage/batch`: `400`.

Neu: `POST /vorhersage/batch` – mehrere Weine in einer Anfrage.

Tests der API (brauchen `models/modell.joblib`):

    pytest tests/test_api.py -v

In CI laufen die API-Tests im Job `pipeline`, direkt nach dem Quality Gate –
mit genau dem Modell, das CI gerade gebaut hat.


## Deployment auf Render (ab Tag 16)

Die Wein-API läuft als Web-Service auf [Render](https://render.com) (PaaS, kostenloser Tarif).

| Einstellung | Wert |
|---|---|
| Language | Python 3 (Version aus `.python-version`: 3.12) |
| Branch | `main` |
| Region | Frankfurt (EU Central) |
| Build Command | `pip install -r requirements-api.txt && python src/daten_exportieren.py && python src/pipeline/validieren.py && python src/pipeline/vorbereiten.py && python src/pipeline/trainieren.py` |
| Start Command | `uvicorn api.app:app --host 0.0.0.0 --port $PORT` |
| Health Check Path | `/health` |
| Auto-Deploy | After CI Checks Pass |

Render baut das Modell beim Deploy mit den Skripten der Pipeline neu (ohne DVC).
CI prüft vorher, dass die Pipeline reproduzierbar ist.

Hinweis: Der kostenlose Service schläft nach 15 Minuten ohne Anfrage ein.
Die erste Anfrage danach dauert etwa eine Minute.