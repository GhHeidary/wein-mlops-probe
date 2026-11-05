# Datei: tests/test_modell.py – in VS Code einfügen und speichern
# Wir testen, ob ein Modell mit unseren Parametern gut genug ist (Mindestqualität).

from pathlib import Path

import yaml
from sklearn.datasets import load_wine
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

MINDEST_GENAUIGKEIT = 0.90


def test_modell_ist_gut_genug():
    # Wir lesen dieselben Parameter wie die Pipeline.
    params = yaml.safe_load(Path("params.yaml").read_text(encoding="utf-8"))
    p_vor = params["vorbereiten"]
    p_train = params["trainieren"]

    daten = load_wine(as_frame=True).frame
    train, test = train_test_split(
        daten,
        test_size=p_vor["test_size"],
        random_state=p_vor["random_state"],
        stratify=daten["target"],
    )

    modell = RandomForestClassifier(
        n_estimators=p_train["n_estimators"],
        max_depth=p_train["max_depth"],
        random_state=p_train["random_state"],
    )
    modell.fit(train.drop(columns="target"), train["target"])

    genauigkeit = accuracy_score(test["target"], modell.predict(test.drop(columns="target")))
    assert genauigkeit >= MINDEST_GENAUIGKEIT, f"Genauigkeit {genauigkeit:.2%} ist zu niedrig"