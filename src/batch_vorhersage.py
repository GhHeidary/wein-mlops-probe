# Datei: src/batch_vorhersage.py – in VS Code einfügen und speichern
# Batch-Deployment (ab Tag 14): Wir bewerten viele Weine auf einmal aus einer CSV-Datei.
# Aufruf:  python src/batch_vorhersage.py [eingabe.csv]

import sys
from pathlib import Path

import joblib
import pandas as pd

EINGABE = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("beispiele/neue_weine.csv")
AUSGABE = Path("ausgabe/vorhersagen.csv")

# Wir laden das Modell aus der Pipeline (geprüft vom Quality Gate).
# joblib kann beim Laden Code ausführen – wir laden nur unser eigenes Modell.
modell = joblib.load("models/modell.joblib")

weine = pd.read_csv(EINGABE)
print(f"Gelesen: {EINGABE} mit {len(weine)} Weinen")

# Vorhersage für alle Zeilen auf einmal
ergebnis = weine.copy()
ergebnis["klasse"] = modell.predict(weine)
ergebnis["wahrscheinlichkeit"] = modell.predict_proba(weine).max(axis=1).round(2)

AUSGABE.parent.mkdir(parents=True, exist_ok=True)
ergebnis.to_csv(AUSGABE, index=False)

print(ergebnis[["alcohol", "proline", "klasse", "wahrscheinlichkeit"]].to_string())
print(f"Gespeichert: {AUSGABE}")