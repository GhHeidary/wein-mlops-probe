# Datei: src/quality_gate.py – in VS Code einfügen und speichern
# Quality Gate (ab Tag 13): Ist das Modell aus der Pipeline gut genug?
# Wir vergleichen metrics.json mit den Mindestwerten aus params.yaml.
# Exit-Code 0 = bestanden, 1 = nicht bestanden. So kann CI den Lauf stoppen.

import json
import os
import sys
from pathlib import Path

import yaml

metriken = json.loads(Path("metrics.json").read_text(encoding="utf-8"))
grenzen = yaml.safe_load(Path("params.yaml").read_text(encoding="utf-8"))["quality_gate"]

# Welche Metrik prüfen wir gegen welchen Mindestwert?
pruefungen = [
    ("genauigkeit", metriken["genauigkeit"], grenzen["min_genauigkeit"]),
    ("f1_makro", metriken["f1_makro"], grenzen["min_f1_makro"]),
]

zeilen = []
bestanden = True
for name, wert, minimum in pruefungen:
    ok = wert >= minimum
    bestanden = bestanden and ok
    zeilen.append(f"| {name} | {wert:.4f} | {minimum:.2f} | {'ok' if ok else 'ZU NIEDRIG'} |")

ergebnis = "BESTANDEN" if bestanden else "NICHT BESTANDEN"
tabelle = "\n".join(
    ["| Metrik | Wert | Minimum | Ergebnis |", "|---|---|---|---|", *zeilen]
)

print(f"Quality Gate: {ergebnis}")
print(tabelle)

# Auf GitHub schreiben wir die Tabelle zusätzlich in die Zusammenfassung des Runs.
zusammenfassung = os.environ.get("GITHUB_STEP_SUMMARY")
if zusammenfassung:
    with open(zusammenfassung, "a", encoding="utf-8") as datei:
        datei.write(f"## Quality Gate: {ergebnis}\n\n{tabelle}\n")

# Nicht bestanden: Exit-Code 1 macht den Schritt in CI rot.
if not bestanden:
    sys.exit(1)