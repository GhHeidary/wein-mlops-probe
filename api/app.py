# Datei: api/app.py – in VS Code einfügen und speichern
# Unsere erste Modell-API mit FastAPI (ab Tag 14).
# Start im Projektordner:  uvicorn api.app:app --reload

import json
from pathlib import Path

import joblib
import pandas as pd
import yaml
from fastapi import FastAPI
from pydantic import BaseModel, Field

# Die drei Klassen im Wine-Datensatz sind drei Rebsorten aus Italien.
KLASSEN = {0: "Sorte 1", 1: "Sorte 2", 2: "Sorte 3"}

app = FastAPI(title="Wein-API", description="Vorhersage der Weinsorte", version="0.1.0")

# Wir laden das Modell EINMAL beim Start – nicht bei jeder Anfrage.
# joblib kann beim Laden Code ausführen – wir laden nur unser eigenes Modell.
modell = joblib.load("models/modell.joblib")


class Wein(BaseModel):
    """Die 13 Messwerte eines Weins – dieselben Spalten wie in data/raw/wein.csv."""

    alcohol: float
    malic_acid: float
    ash: float
    alcalinity_of_ash: float
    magnesium: float
    total_phenols: float
    flavanoids: float
    nonflavanoid_phenols: float
    proanthocyanins: float
    color_intensity: float
    hue: float
    # Der Spaltenname enthält "/" – in Python geht das nicht.
    # Mit alias heißt das Feld in JSON trotzdem so wie die Spalte.
    od280_od315_of_diluted_wines: float = Field(alias="od280/od315_of_diluted_wines")
    proline: float


@app.get("/")
def startseite():
    return {"nachricht": "Die Wein-API läuft", "dokumentation": "/docs"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/modell")
def modell_info():
    # Wir zeigen, welches Modell läuft: Parameter und Ergebnis aus der Pipeline.
    params = yaml.safe_load(Path("params.yaml").read_text(encoding="utf-8"))
    metriken = json.loads(Path("metrics.json").read_text(encoding="utf-8"))
    return {"parameter": params["trainieren"], "metriken": metriken}


@app.get("/klassen/{nummer}")
def klasse(nummer: int):
    # Pfad-Parameter: Die Nummer steht direkt im Pfad, zum Beispiel /klassen/2.
    return {"nummer": nummer, "name": KLASSEN.get(nummer, "unbekannt")}


@app.get("/beispiele")
def beispiele(anzahl: int = 2):
    # Query-Parameter: steht nach dem ?, zum Beispiel /beispiele?anzahl=3.
    weine = pd.read_csv("beispiele/neue_weine.csv").head(anzahl)
    return weine.to_dict(orient="records")


@app.post("/vorhersage")
def vorhersage(wein: Wein):
    # by_alias=True: Wir bekommen die Spaltennamen genau wie beim Training.
    daten = pd.DataFrame([wein.model_dump(by_alias=True)])
    klasse = int(modell.predict(daten)[0])
    wahrscheinlichkeit = float(modell.predict_proba(daten).max())
    return {
        "klasse": klasse,
        "name": KLASSEN[klasse],
        "wahrscheinlichkeit": round(wahrscheinlichkeit, 2),
    }