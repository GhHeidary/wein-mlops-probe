# wein-mlops

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

## Tests (ab Tag 10)

Tests lokal ausführen:

    pytest -v

Die Tests laufen auch automatisch bei jedem Push und Pull Request auf `main`
(GitHub Actions, Datei `.github/workflows/ci.yml`). Ergebnis: Tab **Actions** auf GitHub.