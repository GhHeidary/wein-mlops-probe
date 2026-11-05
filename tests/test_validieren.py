# Datei: tests/test_validieren.py – in VS Code einfügen und speichern
# Wir testen die Prüfregeln aus src/pipeline/validieren.py.

import pytest
from sklearn.datasets import load_wine

from src.pipeline.validieren import pruefe_daten


@pytest.fixture
def gute_daten():
    """Der vollständige Wine-Datensatz: 178 Weine, 13 Merkmale und target."""
    return load_wine(as_frame=True).frame


def test_gute_daten_haben_keine_fehler(gute_daten):
    assert pruefe_daten(gute_daten) == []


def test_alkohol_zu_hoch_wird_erkannt(gute_daten):
    gute_daten.loc[0, "alcohol"] = 45.0
    fehler = pruefe_daten(gute_daten)
    assert len(fehler) == 1
    assert "Alkohol" in fehler[0]


def test_fehlende_spalte_wird_erkannt(gute_daten):
    daten = gute_daten.drop(columns="proline")
    fehler = pruefe_daten(daten)
    assert any("proline" in f for f in fehler)


def test_zu_wenige_zeilen_werden_erkannt(gute_daten):
    fehler = pruefe_daten(gute_daten.head(50))
    assert any("Zu wenige Zeilen" in f for f in fehler)


def test_leere_werte_werden_erkannt(gute_daten):
    gute_daten.loc[3, "magnesium"] = None
    fehler = pruefe_daten(gute_daten)
    assert any("Leere Werte" in f for f in fehler)


def test_unbekannte_klasse_wird_erkannt(gute_daten):
    gute_daten.loc[5, "target"] = 7
    fehler = pruefe_daten(gute_daten)
    assert any("Unbekannte Klassen" in f for f in fehler)


def test_negative_werte_werden_erkannt(gute_daten):
    gute_daten.loc[2, "magnesium"] = -5.0
    fehler = pruefe_daten(gute_daten)
    assert any("Negative Werte" in f for f in fehler)