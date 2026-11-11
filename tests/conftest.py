"""Gemeinsame Fixtures: die Mini-Instanz, an der jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b): das Handbeispiel der App.

Depot (0, 0) und sieben Kunden auf einem Gitter, Entfernung = Manhattan-Abstand = Fahrzeit, Bedienzeit 2, Kapazität 6, Rückkehr bis 38; Dualpreise der ersten Runde 2·d(0, i).
Von Hand nachgerechnet, zum Beispiel: Kunde 7 liegt bei (3, 2): Entfernung zum Depot 3 + 2 = 5, Fenster [8, 20], Dualpreis 2·5 = 10.
Das Label „Weg 7“ hat Zeit max(5, 8) = 8 (Warten bis zum Fensteranfang), Kosten 5 − 10 = −5, Last 2.
Von Kunde 7 nach Kunde 6 (2, 1): Entfernung 1 + 1 = 2; Ankunft 8 + 2 (Bedienzeit) + 2 = 12, Fenster [11, 21]: das Label „Weg 7 → 6“ hat Zeit 12, Kosten −5 + 2 − 6 = −9, Last 2 + 1 = 3.
Der Weg 7 → 6 → 7 → 6 (ein Kreis): Entfernungen 5 + 2 + 2 + 2 + 3 = 14, Dualpreise 10 + 6 + 10 + 6 = 32, reduzierte Kosten 14 − 32 = −18; Zeiten 8, 12, 16, 20 (je Besuch 2 Bedienzeit plus 2 Fahrzeit), Last 2, 3, 5, 6."""

import random
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import kip_scenario as S  # noqa: E402
from kip_scenario import Instanz  # noqa: E402


@pytest.fixture
def hand():
    return S.handbeispiel()


@pytest.fixture
def hand_dual():
    return S.hand_dualpreise(10)


def gitter_instanz(seed: int):
    """Kleine zufällige Gitterinstanz mit ganzen Zahlen (4 bis 6 Kunden, Fenster, Last, Dualpreise) für die Orakeltests.

    Rückgabe (Instanz, Dualpreise). Alles ganzzahlig, damit Gleichstände exakt sind; Kunden dürfen am selben Ort liegen (Entfernung 0)."""
    rng = random.Random(seed)
    n = rng.randint(4, 6)
    felder = [(rng.randint(0, 9), rng.randint(0, 9)) for _ in range(n)]
    punkte = ((5, 5), *felder)
    dist = tuple(tuple(abs(a[0] - b[0]) + abs(a[1] - b[1]) for b in punkte) for a in punkte)
    horizont, svc = 40, 2
    frueh, spaet = [0], [horizont]
    for j in range(1, n + 1):
        e = rng.randint(dist[0][j], 24)
        spaet_max = horizont - svc - dist[0][j]
        frueh.append(e)
        spaet.append(min(spaet_max, e + rng.randint(3, 20)))
    last = (0,) + tuple(rng.randint(1, 4) for _ in range(n))
    inst = Instanz(n, punkte, dist, last, tuple(frueh), tuple(spaet), horizont, svc, 9, 0.0)
    dual = (0,) + tuple(rng.randint(6, 20) for _ in range(n))
    return inst, dual
