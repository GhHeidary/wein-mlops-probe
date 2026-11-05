# Datei: src/pipeline/validieren.py – in VS Code einfügen und speichern
# Stufe 1 der Pipeline: Wir prüfen die Rohdaten, bevor wir damit arbeiten.
# Ab Tag 10 stehen die Regeln in einer Funktion. So können wir sie mit pytest testen.

import json
import sys
from pathlib import Path

import pandas as pd

QUELLE = Path("data/raw/wein.csv")
BERICHT = Path("reports/validierung.json")

MERKMALE = [
    "alcohol", "malic_acid", "ash", "alcalinity_of_ash", "magnesium",
    "total_phenols", "flavanoids", "nonflavanoid_phenols", "proanthocyanins",
    "color_intensity", "hue", "od280/od315_of_diluted_wines", "proline",
]
MINDEST_ZEILEN = 100


def pruefe_daten(daten):
    """Prüft eine Tabelle mit Weindaten. Gibt eine Liste mit Fehlern zurück (leer = alles gut)."""
    fehler = []

    # 1. Sind alle Spalten da?
    fehlende = [s for s in MERKMALE + ["target"] if s not in daten.columns]
    if fehlende:
        fehler.append(f"Spalten fehlen: {fehlende}")

    # 2. Gibt es genug Zeilen?
    if len(daten) < MINDEST_ZEILEN:
        fehler.append(f"Zu wenige Zeilen: {len(daten)} (mindestens {MINDEST_ZEILEN})")

    # 3. Gibt es leere Werte?
    leer = int(daten.isna().sum().sum())
    if leer > 0:
        fehler.append(f"Leere Werte: {leer}")

    # 4. Gibt es nur die Klassen 0, 1 und 2?
    if "target" in daten.columns:
        falsche = sorted(set(daten["target"].dropna().unique()) - {0, 1, 2})
        if falsche:
            fehler.append(f"Unbekannte Klassen: {falsche}")

    # 5. Liegt der Alkoholgehalt in einem sinnvollen Bereich?
    if "alcohol" in daten.columns:
        ausserhalb = int(((daten["alcohol"] < 8) | (daten["alcohol"] > 16)).sum())
        if ausserhalb > 0:
            fehler.append(f"Alkohol außerhalb 8 bis 16 %: {ausserhalb} Zeilen")

    return fehler


def main():
    daten = pd.read_csv(QUELLE)
    fehler = pruefe_daten(daten)

    # Wir schreiben einen Bericht – auch wenn es Fehler gibt.
    BERICHT.parent.mkdir(parents=True, exist_ok=True)
    bericht = {"zeilen": len(daten), "spalten": daten.shape[1], "ok": not fehler, "fehler": fehler}
    BERICHT.write_text(json.dumps(bericht, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if fehler:
        print("Validierung FEHLGESCHLAGEN:")
        for f in fehler:
            print(f"  - {f}")
        # Ein Exit-Code ungleich 0 stoppt die Pipeline.
        sys.exit(1)

    print(f"Validierung OK: {len(daten)} Zeilen, {daten.shape[1]} Spalten, keine Fehler")


# Dieser Teil läuft nur, wenn wir das Skript direkt starten (dvc repro),
# nicht, wenn pytest die Funktion importiert.
if __name__ == "__main__":
    main()