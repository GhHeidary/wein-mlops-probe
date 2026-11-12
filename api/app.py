# Datei: api/app.py – in VS Code einfügen und speichern
# Unsere Modell-API (Stand Tag 15): Wertebereiche, Beispiel, Fehler, Antwortformat, Batch.
# Start im Projektordner:  uvicorn api.app:app --reload

import json
from pathlib import Path

import joblib
import pandas as pd
import yaml
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field

KLASSEN = {0: "Sorte 1", 1: "Sorte 2", 2: "Sorte 3"}

# Dieser Wein erscheint in /docs als Beispiel (erster Wein aus beispiele/neue_weine.csv).
BEISPIEL = {
    "alcohol": 14.23, "malic_acid": 1.71, "ash": 2.43, "alcalinity_of_ash": 15.6,
    "magnesium": 127.0, "total_phenols": 2.8, "flavanoids": 3.06,
    "nonflavanoid_phenols": 0.28, "proanthocyanins": 2.29, "color_intensity": 5.64,
    "hue": 1.04, "od280/od315_of_diluted_wines": 3.92, "proline": 1065.0,
}

app = FastAPI(title="Wein-API", description="Vorhersage der Weinsorte", version="0.2.0")

# Wir laden das Modell einmal beim Start.
modell = joblib.load("models/modell.joblib")


class Wein(BaseModel):
    """Die 13 Messwerte eines Weins. Grenzen: Trainingsdaten, nach außen gerundet."""

    model_config = ConfigDict(json_schema_extra={"examples": [BEISPIEL]})

    alcohol: float = Field(ge=10, le=16, description="Alkohol in %")
    malic_acid: float = Field(ge=0.5, le=7)
    ash: float = Field(ge=1, le=4)
    alcalinity_of_ash: float = Field(ge=8, le=35)
    magnesium: float = Field(ge=60, le=180)
    total_phenols: float = Field(ge=0.5, le=4.5)
    flavanoids: float = Field(ge=0.2, le=6)
    nonflavanoid_phenols: float = Field(ge=0.1, le=0.8)
    proanthocyanins: float = Field(ge=0.3, le=4)
    color_intensity: float = Field(ge=1, le=14)
    hue: float = Field(ge=0.4, le=2)
    od280_od315_of_diluted_wines: float = Field(
        ge=1, le=4.5, alias="od280/od315_of_diluted_wines"
    )
    proline: float = Field(ge=200, le=2000)


class Vorhersage(BaseModel):
    """So sieht jede Antwort einer Vorhersage aus."""

    klasse: int
    name: str
    wahrscheinlichkeit: float


def vorhersagen(weine: list[Wein]) -> list[Vorhersage]:
    # Eine Tabelle mit einer Zeile pro Wein – mit den Spaltennamen aus dem Training.
    daten = pd.DataFrame([w.model_dump(by_alias=True) for w in weine])
    klassen = modell.predict(daten)
    sicherheit = modell.predict_proba(daten).max(axis=1)
    return [
        Vorhersage(klasse=int(k), name=KLASSEN[int(k)], wahrscheinlichkeit=round(float(p), 2))
        for k, p in zip(klassen, sicherheit)
    ]


@app.get("/", tags=["Info"])
def startseite():
    return {"nachricht": "Die Wein-API läuft", "dokumentation": "/docs"}


@app.get("/health", tags=["Info"])
def health():
    return {"status": "ok"}


@app.get("/modell", tags=["Info"])
def modell_info():
    params = yaml.safe_load(Path("params.yaml").read_text(encoding="utf-8"))
    metriken = json.loads(Path("metrics.json").read_text(encoding="utf-8"))
    return {"parameter": params["trainieren"], "metriken": metriken}


@app.get("/klassen/{nummer}", tags=["Info"])
def klasse(nummer: int):
    if nummer not in KLASSEN:
        # Eigener Fehler: Statuscode 404 und eine klare Meldung.
        raise HTTPException(status_code=404, detail=f"Klasse {nummer} gibt es nicht. Erlaubt: 0, 1, 2")
    return {"nummer": nummer, "name": KLASSEN[nummer]}


@app.get("/beispiele", tags=["Info"])
def beispiele(anzahl: int = 2):
    weine = pd.read_csv("beispiele/neue_weine.csv").head(anzahl)
    return weine.to_dict(orient="records")


@app.post("/vorhersage", response_model=Vorhersage, tags=["Vorhersage"])
def vorhersage(wein: Wein):
    return vorhersagen([wein])[0]


@app.post("/vorhersage/batch", response_model=list[Vorhersage], tags=["Vorhersage"])
def vorhersage_batch(weine: list[Wein]):
    if not weine:
        raise HTTPException(status_code=400, detail="Die Liste ist leer.")
    return vorhersagen(weine)