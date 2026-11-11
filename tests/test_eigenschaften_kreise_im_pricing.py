"""Eigenschaftstests (ORACLE-PLAYBOOK §5.2): Aussagen, die für das Verfahren gelten müssen, ohne dass man das richtige Ergebnis kennt.

Je Eigenschaft 15 bis 80 Instanzen mit festem Seed, plus Randfälle; jede Eigenschaft ist eine belegte Aussage über das Verfahren (mit ihren Voraussetzungen), nicht nur das heutige Verhalten des Codes."""

import json
import os
import random
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
from scipy.optimize import linprog

import kip_algorithm as A
import kip_evaluation as E
import kip_master as M
import kip_scenario as S
from conftest import gitter_instanz
from kip_scenario import Instanz

ROOT = Path(__file__).resolve().parent.parent


def _zufall(n, seed, breite):
    return S.make_instance(n, seed, breite)


def test_bound_with_cycles_is_never_above_the_elementary_bound():
    """Jede elementare Route ist auch bei Gedächtnis 1 zulässig: die Schranke (ein Minimum über mehr Spalten) kann nur tiefer oder gleich liegen. 30 Instanzen, n = 6 bis 10, Breiten 40, 100, 200."""
    for seed in range(30):
        inst = _zufall(6 + seed % 5, seed, (40, 100, 200)[seed % 3])
        z1 = M.spaltenerzeugung(inst, 1)["schranke"]
        ze = M.spaltenerzeugung(inst, inst.n)["schranke"]
        assert z1 <= ze + 1e-7, (seed, z1, ze)


def test_bound_does_not_fall_when_the_memory_grows():
    """Gedächtnis k = 1, 2, 3, n mit den k − 1 nächsten Kunden: die Mengen wachsen mit k, die zulässigen Routen werden weniger, die Schranke sinkt nie. 20 Instanzen, n = 7 bis 9, Breiten 100 und 200."""
    for seed in range(20):
        inst = _zufall(7 + seed % 3, seed, (100, 200)[seed % 2])
        werte = [M.spaltenerzeugung(inst, k)["schranke"] for k in (1, 2, 3, inst.n)]
        assert all(a <= b + 1e-7 for a, b in zip(werte, werte[1:])), (seed, werte)


def test_best_reduced_cost_with_cycles_is_never_above_the_elementary_one():
    for seed in range(60):
        inst, dual = gitter_instanz(seed)
        a = A.price(inst, dual, 1, eps=0, neg=0).bester_wert
        b = A.price(inst, dual, inst.n, eps=0, neg=0).bester_wert
        assert a <= b, seed


def test_no_route_repeats_a_customer_directly_and_every_route_is_feasible():
    """Jede Route des Pricings und jede neue Spalte der Spaltenerzeugung hält Fenster, Last, Horizont und die Regel „nicht i direkt nach i“ ein; elementar kommt kein Kunde doppelt vor."""
    for seed in range(20):
        inst = _zufall(8 + seed % 4, seed, (40, 100, 200)[seed % 3])
        dual = S.dualpreise_erste_runde(inst)
        for k in (1, inst.n):
            nb = E.nachbarn_mengen(inst, k)
            for _rc, route in A.price(inst, dual, k).routen:
                assert A.pruefe_route(inst, route, nb) is None, (seed, k, route)
                assert all(a != b for a, b in zip(route, route[1:]))
                assert k == 1 or not A.hat_kreis(route)
        for route in M.neue_spalten(M.spaltenerzeugung(inst, 1), inst.n):
            assert A.pruefe_route(inst, route, E.nachbarn_mengen(inst, 1)) is None, (seed, route)


def test_renumbering_the_customers_changes_neither_bound_nor_best_value():
    """Umnummerieren der Kunden ändert den besten Wert und die Schranke nicht (die Zahl der Labels kann sich ändern: Gleichstände in der Warteschlange hängen an den Nummern)."""
    for seed in range(15):
        inst, dual = gitter_instanz(seed)
        order = [0] + random.Random(seed).sample(range(1, inst.n + 1), inst.n)     # neuer Kunde p ist der alte Kunde order[p]

        def umnummeriert(werte):
            return tuple(werte[order[p]] for p in range(inst.n + 1))
        dist2 = tuple(tuple(inst.dist[order[p]][order[q]] for q in range(inst.n + 1)) for p in range(inst.n + 1))
        inst2 = Instanz(inst.n, umnummeriert(inst.punkte), dist2, umnummeriert(inst.last), umnummeriert(inst.frueh), umnummeriert(inst.spaet), inst.horizont, inst.bedienzeit, inst.kapazitaet, 0.0)
        dual2 = umnummeriert(dual)
        for k in (1, inst.n):
            assert A.price(inst, dual, k, eps=0, neg=0).bester_wert == A.price(inst2, dual2, k, eps=0, neg=0).bester_wert, (seed, k)
        assert M.spaltenerzeugung(inst, 1)["schranke"] == pytest.approx(M.spaltenerzeugung(inst2, 1)["schranke"], rel=1e-9)


def _zahl_teilwege(inst):
    """Zahl aller zulässigen Teilwege ohne direkte Wiederholung (Fenster und Last eingehalten): so viele Labels entstünden ohne Dominanz."""
    zaehler = [0]

    def rec(i, t, q, vorher):
        for j in range(1, inst.n + 1):
            q2 = q + inst.last[j]
            ank = t + (inst.bedienzeit if i != 0 else 0) + inst.dist[i][j]
            if j == vorher or q2 > inst.kapazitaet or ank > inst.spaet[j]:
                continue
            zaehler[0] += 1
            rec(j, max(ank, inst.frueh[j]), q2, j)

    rec(0, 0, 0, 0)
    return zaehler[0]


def _master(inst, routen, gleich):
    a = np.zeros((inst.n, len(routen)))
    kosten = [A.weg_laenge(inst, r) for r in routen]
    for c, r in enumerate(routen):
        for j in r:
            a[j - 1, c] += 1
    if gleich:
        res = linprog(kosten, A_eq=a, b_eq=np.ones(inst.n), bounds=(0, None), method="highs")
    else:
        res = linprog(kosten, A_ub=-a, b_ub=-np.ones(inst.n), bounds=(0, None), method="highs")
    return None if res.status != 0 else res.fun


def test_covering_equals_partitioning_with_metric_costs_for_elementary_routes():
    """Bei metrischen Kosten (Manhattan-Abstand, Dreiecksungleichung) und elementaren Routen ändert Weglassen eines Kunden Fenster und Last nicht zum Schlechteren: Überdeckung gleich Partitionierung.
    Handbeispiel und 20 Gitterinstanzen mit allen Kunden erreichbar (n = 4 bis 6)."""
    hand = S.handbeispiel()
    routen = A.alle_routen(hand, True, 0)
    assert _master(hand, routen, False) == pytest.approx(_master(hand, routen, True), rel=1e-9) == pytest.approx(30.0)
    gepruefte = 0
    for seed in range(20):
        inst, _ = gitter_instanz(seed)
        routen = A.alle_routen(inst, True, 0)
        ueber, partition = _master(inst, routen, False), _master(inst, routen, True)
        assert partition is not None and ueber == pytest.approx(partition, rel=1e-9), seed
        gepruefte += 1
    assert gepruefte == 20


def test_covering_equals_partitioning_with_cycles_on_the_hand_example():
    hand = S.handbeispiel()
    routen = A.alle_routen(hand, False, 0)
    assert _master(hand, routen, False) == pytest.approx(83 / 3, rel=1e-9) == pytest.approx(_master(hand, routen, True), rel=1e-9)


def test_first_round_cycle_route_has_exactly_double_the_reduced_cost_of_the_simple_route():
    """Mit den Dualpreisen der Einzelfahrten (2 d(0, i)) gilt für 0-i-j-i-0 gegenüber 0-i-j-0: reduzierte Kosten 2 (d(i,j) − d(0,i) − d(0,j)), also genau das Doppelte (wenn beide zulässig sind).
    Alle Paare (i, j) mit zulässiger Kreisroute auf 25 Zufallsinstanzen mit n = 8 und dem Handbeispiel."""
    paare = 0
    for inst in [S.handbeispiel()] + [_zufall(8, s, (100, 200)[s % 2]) for s in range(25)]:
        dual = S.dualpreise_erste_runde(inst)
        for i in range(1, inst.n + 1):
            for j in range(1, inst.n + 1):
                if i == j or A.pruefe_route(inst, (i, j, i), None) is not None:
                    continue
                kreis, einfach = A.route_kosten(inst, dual, (i, j, i)), A.route_kosten(inst, dual, (i, j))
                assert kreis == pytest.approx(2 * einfach, abs=1e-9) and kreis == pytest.approx(2 * (inst.dist[i][j] - inst.dist[0][i] - inst.dist[0][j]), abs=1e-9)
                paare += 1
    assert paare > 100


def test_every_rule_acts_on_at_least_one_instance():
    """Zweig-Test (DEMO-PLAYBOOK §0 und §1b): die Regel „Kreise erlaubt“ gegenüber elementar, die Kapazität, das Zeitfenster und die Dominanz ändern auf mindestens einer Instanz das Ergebnis."""
    kreis_wirkt = kapazitaet_wirkt = fenster_wirkt = dominanz_wirkt = 0
    for seed in range(40):
        inst, dual = gitter_instanz(seed)
        b1 = A.price(inst, dual, 1, eps=0, neg=0)
        be = A.price(inst, dual, inst.n, eps=0, neg=0)
        kreis_wirkt += b1.bester_wert < be.bester_wert
        gross = Instanz(inst.n, inst.punkte, inst.dist, inst.last, inst.frueh, inst.spaet, inst.horizont, inst.bedienzeit, 10 ** 6, 0.0)
        kapazitaet_wirkt += A.price(gross, dual, 1, eps=0, neg=0).bester_wert < b1.bester_wert
        weit = Instanz(inst.n, inst.punkte, inst.dist, inst.last, inst.frueh, tuple([inst.horizont] * (inst.n + 1)), inst.horizont, inst.bedienzeit, inst.kapazitaet, 0.0)
        fenster_wirkt += A.price(weit, dual, 1, eps=0, neg=0).bester_wert < b1.bester_wert
        dominanz_wirkt += b1.dominiert > 0 and b1.erzeugt - 1 < _zahl_teilwege(inst)
    assert kreis_wirkt >= 1 and kapazitaet_wirkt >= 1 and fenster_wirkt >= 1 and dominanz_wirkt >= 1


def test_same_seed_gives_the_same_output_in_two_processes_with_different_hash_randomisation():
    code = ("import json, sys; sys.path.insert(0, sys.argv[1]); import kip_evaluation as E; z = E.live_lauf(9, 100, 3); "
            "print(json.dumps([z['k1']['labels'], z['k1']['mit_kreis'], z['k1']['spalten'], round(z['k1']['schranke'], 6), z['elem']['labels'], round(z['elem']['schranke'], 6)]))")
    ausgaben = []
    for hashseed in ("1", "2"):
        env = {**os.environ, "PYTHONHASHSEED": hashseed}
        p = subprocess.run([sys.executable, "-c", code, str(ROOT)], capture_output=True, text=True, env=env, timeout=300)
        assert p.returncode == 0, p.stderr
        ausgaben.append(json.loads(p.stdout.strip().splitlines()[-1]))
    assert ausgaben[0] == ausgaben[1]
