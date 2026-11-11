"""Orakel-Test kreise-im-pricing-demo (ORACLE-PLAYBOOK §2/§5, DEMO-PLAYBOOK §12): unabhängiger Rechenweg für Pricing und Schranke.

Das Orakel zählt ALLE zulässigen Wege auf (Tiefensuche über Teilwege, ohne Dominanz, ohne Warteschlange) und prüft die Wiederholungsregel (Gedächtnis) nach ihrer
Definition an der Wegfolge, nicht über die Bitmasken des Kerns. Es benutzt weder `price` noch `extend` noch `dominiert` des Kerns, nur die Daten der Instanz.
Der Master des Orakels ist ein eigener LP-Aufruf (scipy, auf den aufgezählten Routen), nicht `master_lp` oder `master_exakt` des Kerns.

Geprüft werden (1) der beste Wert (und die Zulässigkeit des gefundenen Weges) für Gedächtnis 1, 3 und elementar, (2) bei Gedächtnis 1 die Menge der überlebenden Labels je Kunde
gegen die Pareto-Front aller Weg-Labels, (3) die Schranke der Spaltenerzeugung gegen einen Master über alle aufgezählten Routen und (4) die 180 Fälle der Vorabmessung
(60 Zufallsinstanzen mit 7 Kunden, drei Breiten, zufällige Dualpreise): Labeling elementar gegen Tiefensuche, und wie oft k = 1 echt unter dem elementaren Optimum liegt.
Zählungen des Kerns (erzeugte Labels) hängen von der Reihenfolge der Warteschlange ab und haben kein Orakel außer dem Handbeispiel. Ganzzahlige Gitterinstanzen (Gleichstände exakt,
Kunden am selben Ort kommen vor), feste Zufalls-Seeds, unter 10 s."""

import random

import numpy as np
import pytest
from scipy.optimize import linprog

import kip_algorithm as A
import kip_master as M
import kip_scenario as S
from conftest import gitter_instanz


def ng_mengen(inst, k):
    """Nachbarschaften NG(j) nach der Definition: j und die k − 1 nächsten anderen Kunden (Gleichstand: kleinere Nummer)."""
    mengen = {}
    for j in range(1, inst.n + 1):
        andere = sorted((i for i in range(1, inst.n + 1) if i != j), key=lambda i: (inst.dist[j][i], i))
        mengen[j] = {j, *andere[: k - 1]}
    return mengen


def ng_zulaessig(folge, ng):
    """Regel nach der Definition: eine Wiederholung des Kunden v an Stelle p nach einem früheren Besuch an Stelle s ist verboten, wenn v in der Nachbarschaft jedes dazwischen liegenden Kunden steht."""
    p = len(folge) - 1
    for s in range(p):
        if folge[s] == folge[p] and all(folge[p] in ng[folge[x]] for x in range(s + 1, p)):
            return False
    return True


def orakel(inst, dual, k, eps=0):
    """Alle zulässigen Wege: Rückgabe (bester Wert, Weg, {Kunde: Menge der Vektoren (Zeit, Kosten, Last) aller Teilwege}, Liste aller zulässigen Routen)."""
    ng = ng_mengen(inst, k)
    bester = [0, ()]
    vektoren = {j: set() for j in range(1, inst.n + 1)}
    routen = []

    def rec(folge, i, t, q, c):
        if folge:
            vektoren[i].add((t, c, q))
            if t + inst.bedienzeit + inst.dist[i][0] <= inst.horizont + eps:
                routen.append(tuple(folge))
                rc = c + inst.dist[i][0]
                if rc < 0 and (rc, tuple(folge)) < (bester[0], bester[1] or (99,)):
                    bester[0], bester[1] = rc, tuple(folge)
        for j in range(1, inst.n + 1):
            if folge and not ng_zulaessig(folge + [j], ng):
                continue
            q2 = q + inst.last[j]
            if q2 > inst.kapazitaet:
                continue
            ank = t + (inst.bedienzeit if folge else 0) + inst.dist[i][j]
            if ank > inst.spaet[j] + eps:
                continue
            rec(folge + [j], j, max(ank, inst.frueh[j]), q2, c + inst.dist[i][j] - dual[j])

    rec([], 0, 0, 0, 0)
    return bester[0], bester[1], vektoren, routen


def pareto(vektoren):
    """Nicht dominierte, verschiedene Vektoren (Zeit, Kosten, Last): v bleibt, wenn kein anderer Vektor w mit w <= v in allen Stellen existiert."""
    return {v for v in vektoren if not any(w != v and w[0] <= v[0] and w[1] <= v[1] and w[2] <= v[2] for w in vektoren)}


def master_ueber_alle_routen(inst, routen):
    """Eigener Überdeckungs-Master: min c·x mit A x >= 1 über alle aufgezählten Routen (scipy, HiGHS), unabhängig von kip_master."""
    a = np.zeros((inst.n, len(routen)))
    kosten = []
    for c, r in enumerate(routen):
        folge = (0,) + r + (0,)
        kosten.append(sum(inst.dist[x][y] for x, y in zip(folge, folge[1:])))
        for j in r:
            a[j - 1, c] += 1
    res = linprog(kosten, A_ub=-a, b_ub=-np.ones(inst.n), bounds=(0, None), method="highs")
    assert res.status == 0
    return float(res.fun)


def test_best_value_matches_enumeration_on_80_random_instances():
    fehler, faelle = [], 0
    for seed in range(80):
        inst, dual = gitter_instanz(seed)
        for k in (1, 3, inst.n):
            soll, _weg, _v, _r = orakel(inst, dual, k)
            res = A.price(inst, dual, k, eps=0, neg=0)
            faelle += 1
            if res.bester_wert != soll:
                fehler.append((seed, k, res.bester_wert, soll))
            elif res.routen:
                # Bei gleichem Wert kann eine andere der gleich guten Routen herauskommen (gleiche Labels fallen weg): die Route des Kerns muss zulässig sein und den Wert haben.
                nb = [set()] + [ng_mengen(inst, k)[j] for j in range(1, inst.n + 1)]
                route = res.routen[0][1]
                if A.pruefe_route(inst, route, nb, 0) is not None or A.route_kosten(inst, dual, route) != soll:
                    fehler.append((seed, k, "Route", route))
    assert faelle == 240 and not fehler, fehler[:5]


def test_survivors_are_the_pareto_front_of_all_walk_labels_for_k1():
    for seed in range(80):
        inst, dual = gitter_instanz(seed)
        _, _, vektoren, _ = orakel(inst, dual, 1)
        res = A.price(inst, dual, 1, eps=0, neg=0)
        for j in range(1, inst.n + 1):
            assert set(res.ueberlebende[j]) == pareto(vektoren[j]), (seed, j)
            assert len(res.ueberlebende[j]) == len(set(res.ueberlebende[j]))   # keine doppelten Labels überleben


def test_orakel_agrees_with_the_hand_example(hand, hand_dual):
    """Das Orakel selbst am Handbeispiel prüfen: −18 für 7 → 6 → 7 → 6 (Kreise erlaubt), −10 für 2 → 7 → 6 (elementar); 89 bzw. 79 zulässige Wege."""
    wert, weg, _v, routen = orakel(hand, hand_dual, 1)
    assert (wert, weg, len(routen)) == (-18, (7, 6, 7, 6), 89)
    wert, weg, _v, routen = orakel(hand, hand_dual, 7)
    assert (wert, weg, len(routen)) == (-10, (2, 7, 6), 79)


def test_orakel_rule_follows_the_definition():
    ng = {1: {1, 2}, 2: {2, 1}, 3: {3}}
    assert not ng_zulaessig([1, 1], ng)               # sofortige Wiederholung immer verboten
    assert not ng_zulaessig([1, 2, 1], ng)            # 1 steht in der Nachbarschaft von 2: noch bekannt
    assert ng_zulaessig([1, 3, 1], ng)                # 1 steht nicht in der Nachbarschaft von 3: vergessen
    assert ng_zulaessig([1, 2, 3, 2], ng)             # 2 steht nicht in der Nachbarschaft von 3: vergessen
    assert not ng_zulaessig([3, 1, 2, 1], ng)         # die frühere Stelle von 1 liegt vor 2: nur 2 liegt dazwischen, und 1 steht in NG(2)


def test_column_generation_bound_equals_a_master_over_all_enumerated_routes():
    """Die Schranke der Spaltenerzeugung (Kern: HiGHS-Master plus Pricing) gegen einen Master über alle aufgezählten Routen (Orakel: eigene Aufzählung und eigener LP-Aufruf)."""
    zaehler = 0
    for seed in range(25):
        inst, _dual = gitter_instanz(seed)
        for k in (1, inst.n):
            _w, _r, _v, routen = orakel(inst, (0,) + (0,) * inst.n, k)
            soll = master_ueber_alle_routen(inst, routen)
            lauf = M.spaltenerzeugung(inst, k)
            assert lauf["schranke"] == pytest.approx(soll, rel=1e-7, abs=1e-7), (seed, k)
            zaehler += 1
    assert zaehler == 50


def test_exact_master_and_pricing_agree_with_the_orakel_on_the_hand_example(hand):
    """Spaltenerzeugung exakt (Brüche) gegen den eigenen Master über alle aufgezählten Routen: 83/3 mit Kreisen, 30 elementar."""
    for k, soll in ((1, 83 / 3), (7, 30.0)):
        _w, _r, _v, routen = orakel(hand, (0,) * 8, k)
        assert master_ueber_alle_routen(hand, routen) == pytest.approx(soll, rel=1e-9)


def test_vormessung_180_cases_elementary_matches_depth_first_search_and_k1_is_never_above():
    """60 Zufallsinstanzen mit 7 Kunden mal Breiten 30, 80, 200, zufällige Dualpreise 20 bis 70: Labeling elementar gegen Tiefensuche; k = 1 liegt nie über dem elementaren Optimum."""
    abweichung = ueber = echt_darunter = faelle = 0
    for seed in range(60):
        for breite in (30, 80, 200):
            inst = S.make_instance(7, seed, breite)
            rng = random.Random(1000 + seed)
            dual = [0.0] + [rng.uniform(20, 70) for _ in range(inst.n)]
            referenz = orakel(inst, dual, inst.n, eps=1e-9)[0]
            elementar = A.price(inst, dual, inst.n, max_routes=1).bester_wert
            kreise = A.price(inst, dual, 1, max_routes=1).bester_wert
            faelle += 1
            abweichung += abs(elementar - referenz) > 1e-6
            ueber += kreise > referenz + 1e-6
            echt_darunter += kreise < referenz - 1e-6
    assert (faelle, abweichung, ueber) == (180, 0, 0)
    assert echt_darunter == 102
