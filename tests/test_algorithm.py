"""Kern gegen Handrechnung und Gegenproben, die nichts aus dem Kern-Modul benutzen (DEMO-PLAYBOOK §1b und §12).

Jede Regel des Kerns (Erweiterung, Dominanz, Einfügen, Rückverfolgung, Pricing, Master, Spaltenerzeugung) wird an der Mini-Instanz (dem Handbeispiel, siehe conftest.py) gegen Handrechnung geprüft;
die Zahlen des Handbeispiels stehen als Rechnung da, wo es eine gibt."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from fractions import Fraction

import pytest

import kip_algorithm as A
import kip_constants as C
import kip_evaluation as E
import kip_master as M
import kip_scenario as S


def _label(t, c, q, mem, node):
    return [t, c, q, mem, node, None, False]


# --- Erweiterungsregel --------------------------------------------------------------------------------------------------------------------

def test_extend_from_the_depot_has_no_service_time_and_waits_for_the_window(hand, hand_dual):
    ng = A.ng_masks(hand.dist, 7, 1)
    neu, grund = A.extend(hand, hand_dual, ng, _label(0, 0, 0, 0, 0), 7, eps=0)
    # Kunde 7: Entfernung 3 + 2 = 5, Fenster [8, 20]: Zeit 8 (warten), Kosten 5 − 10, Last 2
    assert grund is None and neu[0] == max(3 + 2, 8) and neu[1] == (3 + 2) - 10 and neu[2] == 2 and neu[4] == 7 and neu[3] == 1 << 7


def test_extend_adds_service_time_distance_dual_and_load(hand, hand_dual):
    ng = A.ng_masks(hand.dist, 7, 1)
    l7 = _label(8, -5, 2, 1 << 7, 7)
    neu, grund = A.extend(hand, hand_dual, ng, l7, 6, eps=0)
    # Kunde 6 liegt bei (2, 1): Entfernung 1 + 1 = 2; Ankunft 8 + 2 + 2 = 12, Fenster [11, 21]; Kosten −5 + 2 − 6; Last 2 + 1
    assert grund is None and neu[0] == 8 + 2 + 2 and neu[1] == -5 + 2 - 6 and neu[2] == 2 + 1 and neu[3] == 1 << 6


def test_extend_refuses_by_load_first_and_then_by_window(hand, hand_dual):
    ng = A.ng_masks(hand.dist, 7, 1)
    voll = _label(0, 0, 6, 1 << 1, 1)                      # Last 6 = Kapazität: Kunde 2 (Last 3) passt nicht, Kunde 7 (Last 2) auch nicht
    assert A.extend(hand, hand_dual, ng, voll, 7, eps=0) == (None, "last")
    spaet = _label(100, 0, 0, 1 << 1, 1)                   # Zeit 100: jede Ankunft liegt nach jedem Fensterende
    assert A.extend(hand, hand_dual, ng, spaet, 2, eps=0) == (None, "fenster")


def test_capacity_and_window_limits_are_inclusive(hand, hand_dual):
    ng = A.ng_masks(hand.dist, 7, 1)
    neu, grund = A.extend(hand, hand_dual, ng, _label(0, 0, 4, 1 << 1, 1), 7, eps=0)       # Last 4 + 2 = 6 = Kapazität: erlaubt
    assert grund is None and neu[2] == hand.kapazitaet
    # Ankunft genau am Fensterende: von Kunde 3 nach Kunde 5 (Entfernung 2, Fenster [3, 12]): mit Zeit 8 am Kunden 3 ist die Ankunft 8 + 2 + 2 = 12 = Fensterende (erlaubt), mit Zeit 9 ist sie 13 (zu spät)
    l3 = _label(8, 0, 0, 1 << 3, 3)
    assert A.extend(hand, hand_dual, ng, l3, 5, eps=0)[1] is None
    assert A.extend(hand, hand_dual, ng, _label(9, 0, 0, 1 << 3, 3), 5, eps=0)[1] == "fenster"


def test_every_visit_counts_again_a_repeated_customer_costs_load_and_time_again(hand, hand_dual):
    """Der Kreis 7 → 6 → 7 → 6 aus conftest.py: Zeiten 8, 12, 16, 20, Last 2, 3, 5, 6, reduzierte Kosten 14 − 32."""
    ng = A.ng_masks(hand.dist, 7, 1)
    lab = _label(0, 0, 0, 0, 0)
    zeiten, lasten = [], []
    for j in (7, 6, 7, 6):
        lab, grund = A.extend(hand, hand_dual, ng, lab, j, eps=0)
        assert grund is None
        zeiten.append(lab[0])
        lasten.append(lab[2])
    assert zeiten == [8, 12, 16, 20] and lasten == [2, 3, 5, 6]
    assert A.route_kosten(hand, hand_dual, (7, 6, 7, 6)) == (5 + 2 + 2 + 2 + 3) - (10 + 6 + 10 + 6) == -18
    assert A.route_kosten(hand, hand_dual, (2, 7, 6)) == (3 + 4 + 2 + 3) - (6 + 10 + 6) == -10


def test_memory_k1_forbids_only_the_direct_repetition_and_elementary_forbids_every_repetition(hand):
    m1, m7 = A.ng_masks(hand.dist, 7, 1), A.ng_masks(hand.dist, 7, 7)
    assert all(m1[j] == 1 << j for j in range(1, 8))
    assert all(m7[j] == sum(1 << i for i in range(1, 8)) for j in range(1, 8))


# --- Dominanz ------------------------------------------------------------------------------------------------------------------------------

def test_dominance_rule_on_hand_made_labels():
    o = _label(10, -5, 3, 0b10, 1)
    assert A.dominiert(o, _label(12, -5, 3, 0b10, 1), eps=0)           # gleiche Kosten, spätere Zeit: dominiert
    assert A.dominiert(o, _label(10, -5, 3, 0b10, 1), eps=0)           # gleiches Label: dominiert (das neue fällt weg)
    assert not A.dominiert(o, _label(12, -6, 3, 0b10, 1), eps=0)       # das andere hat kleinere Kosten
    assert not A.dominiert(o, _label(12, -5, 2, 0b10, 1), eps=0)       # das andere hat weniger Last
    assert not A.dominiert(o, _label(9, -5, 3, 0b10, 1), eps=0)        # das andere ist früher
    assert not A.dominiert(_label(10, -5, 3, 0b110, 1), _label(10, -5, 3, 0b10, 1), eps=0)   # o kennt mehr Kunden als das andere: keine Dominanz
    assert A.dominiert(_label(10, -5, 3, 0b10, 1), _label(10, -5, 3, 0b110, 1), eps=0)


def test_insert_label_discards_the_new_label_or_replaces_old_ones():
    labels = [_label(10, -5, 3, 0b10, 1), _label(20, -9, 5, 0b10, 1)]
    von, abgeloest, lebend, v = A.insert_label(labels, [0, 1], _label(12, -5, 3, 0b10, 1), eps=0)
    assert von == 0 and abgeloest == [] and v == 1                                   # Label 0 dominiert das neue: ein Test genügt
    von, abgeloest, lebend, v = A.insert_label(labels, [0, 1], _label(8, -9, 2, 0b10, 1), eps=0)
    assert von is None and abgeloest == [0, 1] and lebend == [] and v == 4 and labels[0][6] and labels[1][6]   # das neue dominiert beide: zwei Tests je Richtung


def test_trace_route_follows_the_predecessors():
    labels = [[0, 0, 0, 0, 0, -1, False], [8, -5, 2, 0, 7, 0, False], [12, -9, 3, 0, 6, 1, False]]
    assert A.trace_route(labels, 2) == (7, 6) and A.trace_route(labels, 0) == ()


# --- Handbeispiel: Pricing mit Kreisen und elementar ------------------------------------------------------------------------------------

def test_hand_example_pricing_with_cycles_counts_and_best_routes(hand, hand_dual):
    res = A.price(hand, hand_dual, 1, eps=0, neg=0)
    assert (res.erzeugt, res.dominiert) == (62, 27 + 5) and res.erzeugt - res.dominiert == 30 and not res.abgebrochen
    assert res.routen[:6] == [(-18, (7, 6, 7, 6)), (-16, (7, 6, 7, 1)), (-14, (5, 3, 5, 1)), (-14, (6, 7, 6, 1)), (-12, (5, 3, 5)), (-12, (6, 7, 6))]
    assert all(A.hat_kreis(r) for _rc, r in res.routen[:6])


def test_hand_example_elementary_pricing(hand, hand_dual):
    res = A.price(hand, hand_dual, 7, eps=0, neg=0)
    assert res.erzeugt == 56 and res.routen[0] == (-10, (2, 7, 6))
    assert not any(A.hat_kreis(r) for _rc, r in res.routen)


def test_hand_example_survivors_are_the_labels_that_were_not_dominated(hand, hand_dual):
    res, prot = E.hand_lauf(1, 10, mit_protokoll=True)
    tab = E.label_tabelle(prot)
    assert len(tab) == res.erzeugt == 62 and sum(1 for z in tab if z["von"] is not None) == 27 and sum(1 for z in tab if z["abgeloest_von"] is not None) == 5
    assert len(E.ueberlebende_tabelle(tab)) == 30 - 1                                # 30 lebende Labels inklusive des Startlabels am Depot
    assert sum(len(x) for x in res.ueberlebende) == 30 - 1


def test_hand_example_enumeration_of_all_feasible_routes(hand, hand_dual):
    wert, weg, wege, kreis, negativ = A.aufzaehlung(hand, hand_dual, False, 0)
    assert (wert, weg, wege, kreis, negativ) == (-18, (7, 6, 7, 6), 89, 10, 68)
    wert, weg, wege, _kreis, _neg = A.aufzaehlung(hand, hand_dual, True, 0)
    assert (wert, weg, wege) == (-10, (2, 7, 6), 79)
    assert all(not A.hat_kreis(r) for r in A.alle_routen(hand, True, 0))


def test_hand_example_pricing_matches_the_enumeration_on_every_dual_of_customer_7(hand):
    for d7 in range(C.HAND_DUAL7_MIN, C.HAND_DUAL7_MAX + 1):
        dual = S.hand_dualpreise(d7)
        for k, elementar in ((1, False), (7, True)):
            res = A.price(hand, dual, k, eps=0, neg=0)
            assert res.bester_wert == A.aufzaehlung(hand, dual, elementar, 0)[0], (d7, k)


def test_route_checker_accepts_feasible_and_rejects_violating_routes(hand):
    nb = E.nachbarn_mengen(hand, 1)
    assert A.pruefe_route(hand, (7, 6, 7, 6), nb, 0) is None
    assert "wiederholt" in A.pruefe_route(hand, (7, 7), nb, 0)
    assert "Fensterende" in A.pruefe_route(hand, (1, 5), nb, 0)               # 5 liegt hinter Kunde 1 zu spät
    assert "Kapazität" in A.pruefe_route(hand, (2, 3, 4), nb, 0)             # Last 3 + 3 + 3 = 9 > 6
    assert A.pruefe_route(hand, (), nb, 0) == "leere Route" and "existiert nicht" in A.pruefe_route(hand, (9,), nb, 0)
    assert A.pruefe_route(replace(hand, horizont=17), (7, 6), None, 0) is None                 # Rückkehr 12 + 2 + 3 = 17 = Horizont: erlaubt
    assert "Horizont" in A.pruefe_route(replace(hand, horizont=16), (7, 6), None, 0)


def test_schedule_of_the_best_route_matches_the_hand_calculation(hand, hand_dual):
    plan = A.fahrplan(hand, hand_dual, (7, 6, 7, 6))
    assert [(z["kunde"], z["besuch"], z["ankunft"], z["beginn"], z["last"]) for z in plan] == [(7, 1, 5, 8, 2), (6, 1, 12, 12, 3), (7, 2, 16, 16, 5), (6, 2, 20, 20, 6)]
    assert [z["kosten"] for z in plan] == [-5, -9, -17, -21] and plan[-1]["kosten"] + hand.dist[6][0] == -18
    a = E.aufstellung(hand, hand_dual, (7, 6, 7, 6))
    assert (a["summe_entfernung"], a["summe_dual"], a["wert"]) == (14, 32, -18)


def test_cycle_helpers():
    assert A.hat_kreis((7, 6, 7, 6)) and not A.hat_kreis((2, 7, 6))
    assert A.doppelte_kunden((7, 6, 7, 6, 1)) == {6: 2, 7: 2} and A.wiederholungen((7, 6, 7, 6, 1)) == 2
    assert A.kuerzester_kreis((7, 6, 7, 6)) == 2 and A.kuerzester_kreis((5, 3, 1, 5)) == 3 and A.kuerzester_kreis((1, 2, 3, 4, 1)) == 4 and A.kuerzester_kreis((1, 2, 3)) is None


# --- Master und Spaltenerzeugung ---------------------------------------------------------------------------------------------------------

def test_exact_master_on_the_single_trips_gives_the_first_round_duals(hand):
    spalten = [(j,) for j in range(1, 8)]
    wert, dual, x = M.master_exakt(7, [A.weg_laenge(hand, r) for r in spalten], spalten)
    assert dual[1:] == [2 * hand.dist[0][j] for j in range(1, 8)] and wert == sum(2 * hand.dist[0][j] for j in range(1, 8)) == 50 and x == [1] * 7


def test_hand_example_column_generation_with_cycles_round_by_round(hand):
    cg = E.hand_spaltenerzeugung(False)
    assert [r["wert"] for r in cg["lauf"]["runden"]] == [50, 41, 33, 33, 32, 29, 28, Fraction(83, 3)]
    assert [r["neue"][0][1] for r in cg["lauf"]["runden"][:-1]] == [(7, 6, 7, 6), (5, 3, 5, 1), (6, 7, 6, 1), (2, 1), (3, 4), (5, 3, 5), (5, 4)]
    assert cg["lauf"]["runden"][-1]["neue"] == [] and cg["schranke"] == Fraction(83, 3)
    assert (cg["runden"], cg["labels"], len(cg["neue"]), cg["mit_kreis"]) == (8, 416, 7, 4)
    assert [(r, x) for r, x in cg["ende"]] == [((7, 6, 7, 6), Fraction(1, 2)), ((2, 1), 1), ((3, 4), Fraction(2, 3)), ((5, 3, 5), Fraction(1, 3)), ((5, 4), Fraction(1, 3))]
    assert [A.kuerzester_kreis(r) for r in cg["neue"] if A.hat_kreis(r)] == [2, 2, 2, 2]


def test_hand_example_column_generation_elementary(hand):
    cg = E.hand_spaltenerzeugung(True)
    assert cg["schranke"] == 30 and cg["runden"] == 7 and cg["labels"] == 326 and cg["mit_kreis"] == 0


def test_hand_example_column_generation_equals_a_master_over_all_routes(hand):
    assert E.hand_gegenprobe(False) == {"wert": Fraction(83, 3), "spalten": 89}
    assert E.hand_gegenprobe(True) == {"wert": 30, "spalten": 79}


def test_the_number_of_hand_rounds_is_the_upper_bound_of_the_round_control():
    assert E.hand_spaltenerzeugung(False)["runden"] == C.HAND_RUNDE_MAX


def test_lp_master_and_exact_master_agree_on_random_column_sets():
    import random
    for seed in range(12):
        rng = random.Random(seed)
        inst = S.make_instance(6, seed, 100)
        spalten = [(j,) for j in range(1, 7)]
        for _ in range(rng.randint(2, 8)):
            spalten.append(tuple(rng.sample(range(1, 7), rng.randint(1, 4))))
        kosten = [round(A.weg_laenge(inst, r) * 1000) for r in spalten]            # ganzzahlig für den exakten Master
        wert_lp, dual_lp, x_lp = M.master_lp(6, kosten, spalten)
        wert_ex, dual_ex, x_ex = M.master_exakt(6, kosten, spalten)
        assert wert_lp == pytest.approx(float(wert_ex), rel=1e-9), seed
        # beide Dualpreise sind zulässig für das Duale und haben denselben Wert
        for dual in (dual_lp, [float(d) for d in dual_ex]):
            assert all(sum(dual[j] * r.count(j) for j in set(r)) <= kosten[c] + 1e-6 for c, r in enumerate(spalten)) and sum(dual[1:]) == pytest.approx(float(wert_ex), rel=1e-9)
        assert all(x >= -1e-12 for x in x_lp) and all(sum(x_ex[c] * r.count(j) for c, r in enumerate(spalten)) >= 1 for j in range(1, 7))


def test_a_cycle_column_counts_the_repeated_customer_twice_in_the_master_matrix():
    a = M._matrix(7, [(7, 6, 7, 6), (2, 1)])
    assert a[6, 0] == 2 and a[5, 0] == 2 and a[1, 1] == 1 and a[0, 1] == 1 and a[:, 0].sum() == 4


# --- Zufallsinstanzen, Obergrenze und Regler-Maximum -------------------------------------------------------------------------------------

def test_random_instance_generator_is_deterministic_and_has_the_documented_ranges():
    a, b = S.make_instance(12, 7, 60), S.make_instance(12, 7, 60)
    assert a == b and a != S.make_instance(12, 8, 60)
    assert all(C.LAST_MIN <= q <= C.LAST_MAX for q in a.last[1:]) and a.last[0] == 0
    assert all(a.spaet[j] - a.frueh[j] <= 60 + 1e-9 and a.frueh[j] >= a.dist[0][j] - 1e-9 for j in range(1, 13))
    assert a.kapazitaet == C.KAPAZITAET and a.horizont == C.HORIZONT and a.bedienzeit == C.BEDIENZEIT


def test_the_cap_stops_a_pricing_call_reproducibly():
    inst = S.make_instance(15, 3, 100)
    dual = S.dualpreise_erste_runde(inst)
    r1 = A.price(inst, dual, 15, max_vergleiche=2000)
    r2 = A.price(inst, dual, 15, max_vergleiche=2000)
    assert r1.abgebrochen and (r1.erzeugt, r1.vergleiche) == (r2.erzeugt, r2.vergleiche)
    r3 = A.price(inst, dual, 15, max_labels=300)
    assert r3.abgebrochen and r3.erzeugt >= 300
    cg = M.spaltenerzeugung(inst, 15, max_vergleiche=2000)
    assert cg["abgebrochen"] and cg["schranke"] is None


def test_worst_case_at_the_slider_maximum_finishes_and_reports_an_abort_instead_of_hanging():
    """Größte Einstellung der Live-Rechnung (n = 20, Breite 200): die elementare Rechnung darf an der Obergrenze enden; geprüft wird nur, dass der Lauf endet (großzügiges Zeitnetz, keine Zeit-Assertion)."""
    with ThreadPoolExecutor(max_workers=1) as pool:
        z = pool.submit(E.live_lauf, C.LIVE_N_MAX, max(C.LIVE_BREITEN), 0).result(timeout=600)
    assert z["fehler"] is None and z["k1"]["schranke"] > 0
    assert z["elem"]["abgebrochen"] or z["elem"]["schranke"] >= z["k1"]["schranke"] - 1e-6
    if z["elem"]["abgebrochen"]:
        assert z["luecke"] is None and z["elem"]["vergleiche"] >= C.LIVE_MAX_VERGLEICHE_ELEMENTAR - 1
