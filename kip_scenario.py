"""Szenario: Instanzen im Stil von Solomon (eigener Generator, nicht die Originalinstanzen) und das Handbeispiel mit sieben Kunden.

Alle Instanzen sind unveränderlich (Tupel). Zufall kommt nur über einen `random.Random`, der aus dem Zufalls-Seed gebildet wird;
das ist derselbe Generator in derselben Reihenfolge der Ziehungen wie in der Vormessung, damit die festen Messreihen in data/ nachrechenbar bleiben (Abschnitt „Abweichungen“ der README)."""

import math
import random
from dataclasses import dataclass
from fractions import Fraction

import kip_constants as C


@dataclass(frozen=True)
class Instanz:
    """Depot = Knoten 0, Kunden 1..n. Zeit und Entfernung sind gleich; `last` ist die Nachfrage (Index 0 = Depot = 0)."""

    n: int
    punkte: tuple          # ((x, y), ...) mit dem Depot zuerst
    dist: tuple            # Entfernungsmatrix (n + 1) x (n + 1)
    last: tuple
    frueh: tuple           # früheste Bedienung je Kunde (Fensteranfang)
    spaet: tuple           # späteste Ankunft je Kunde (Fensterende)
    horizont: float
    bedienzeit: float
    kapazitaet: int
    breite: float = 0.0


def _matrix(punkte, metrik):
    return tuple(tuple(metrik(a, b) for b in punkte) for a in punkte)


def make_instance(n: int, seed: int, breite: float, gruppiert: bool = False, horizont: float = C.HORIZONT, kapazitaet: int = C.KAPAZITAET) -> Instanz:
    """Solomon-artige Instanz: Depot (50, 50), n Kunden im Quadrat 100 x 100, Nachfrage 5 bis 25, Zeitfenster der Breite `breite`.

    Der Fenstermittelpunkt wird gleichverteilt zwischen frühestmöglicher und spätestmöglicher Ankunft gezogen und die Breite darum gelegt
    (an Anfang und Ende auf die erreichbaren Zeiten begrenzt). `gruppiert`: fünf Zentren, Kunden normalverteilt (Streuung 6) um ein Zentrum."""
    rng = random.Random(seed)
    if gruppiert:
        zentren = [(rng.uniform(15, 85), rng.uniform(15, 85)) for _ in range(5)]
        kunden = []
        for _ in range(n):
            cx, cy = rng.choice(zentren)
            kunden.append((min(100.0, max(0.0, rng.gauss(cx, 6))), min(100.0, max(0.0, rng.gauss(cy, 6)))))
    else:
        kunden = [(rng.uniform(0, 100), rng.uniform(0, 100)) for _ in range(n)]
    punkte = tuple([(50.0, 50.0)] + kunden)
    dist = _matrix(punkte, math.dist)
    last = tuple([0] + [rng.randint(C.LAST_MIN, C.LAST_MAX) for _ in range(n)])
    frueh = [0.0] * (n + 1)
    spaet = [horizont] * (n + 1)
    for i in range(1, n + 1):
        lo = dist[0][i]
        hi = horizont - C.BEDIENZEIT - dist[0][i]
        mitte = rng.uniform(lo, hi)
        frueh[i] = max(lo, mitte - breite / 2)
        spaet[i] = min(hi, mitte + breite / 2)
    return Instanz(n, punkte, dist, last, tuple(frueh), tuple(spaet), horizont, C.BEDIENZEIT, kapazitaet, float(breite))


def dualpreise_erste_runde(inst: Instanz) -> tuple:
    """Dualpreise der ersten Spaltenerzeugungsrunde: Startspalten sind die Einzelkunden-Fahrten Depot-i-Depot, ihre Kosten 2 d(0, i) sind die Preise."""
    return (0,) + tuple(2 * inst.dist[0][i] for i in range(1, inst.n + 1))


# ---------------------------------------------------------------------------------------------------------------------------------
# Handbeispiel: Depot (0, 0) und sieben Kunden, Manhattan-Abstand, Fahrzeit = Entfernung (zum Nachrechnen mit dem Stift; ganze Zahlen)
# ---------------------------------------------------------------------------------------------------------------------------------
HAND_PUNKTE = ((0, 0), (-1, 2), (0, 3), (-3, -2), (-1, -2), (-2, -1), (2, 1), (3, 2))
HAND_LAST = (0, 1, 3, 3, 3, 1, 1, 2)
HAND_FRUEH = (0, 18, 3, 5, 20, 3, 11, 8)
HAND_SPAET = (38, 28, 16, 15, 28, 12, 21, 20)
HAND_BEDIENZEIT, HAND_HORIZONT, HAND_KAPAZITAET = 2, 38, 6
HAND_KUNDE_MIT_PREIS = 7          # dieser Kunde bekommt den Dualpreis des Reglers (Experiment 1)


def handbeispiel() -> Instanz:
    """Das Handbeispiel als Instanz (ganze Zahlen); Zeitfenster in `frueh` und `spaet`."""
    dist = _matrix(HAND_PUNKTE, lambda a, b: abs(a[0] - b[0]) + abs(a[1] - b[1]))
    return Instanz(7, HAND_PUNKTE, dist, HAND_LAST, HAND_FRUEH, HAND_SPAET, HAND_HORIZONT, HAND_BEDIENZEIT, HAND_KAPAZITAET, 0.0)


def hand_dualpreise(dual7: int = 10) -> tuple:
    """Dualpreise der ersten Runde des Handbeispiels (2 d(0, i)); Kunde 7 bekommt stattdessen `dual7` (die Voreinstellung 10 ist sein Wert der ersten Runde)."""
    erste = list(dualpreise_erste_runde(handbeispiel()))
    erste[HAND_KUNDE_MIT_PREIS] = dual7
    return tuple(erste)


def bruch(werte) -> list:
    """Ganzzahlige Werte als Brüche (für die exakte Rechnung des Handbeispiels)."""
    return [Fraction(w) for w in werte]
