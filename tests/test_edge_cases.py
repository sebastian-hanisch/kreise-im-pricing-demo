"""Randfälle, an denen Kernroutinen erfahrungsgemäß brechen (DEMO-PLAYBOOK §12): n = 1, n = 2, Last gleich Kapazität, zu enge Fenster, Kunden am selben Ort, Gleichstände, Abbruch an der Obergrenze."""

from dataclasses import replace

import pytest

import kip_algorithm as A
import kip_evaluation as E
import kip_master as M
import kip_scenario as S
from kip_scenario import Instanz


def _instanz(punkte, last, frueh, spaet, kapazitaet=10, horizont=100, svc=2):
    n = len(punkte) - 1
    dist = tuple(tuple(abs(a[0] - b[0]) + abs(a[1] - b[1]) for b in punkte) for a in punkte)
    return Instanz(n, tuple(punkte), dist, (0, *last), (0, *frueh), (horizont, *spaet), horizont, svc, kapazitaet, 0.0)


def test_a_single_customer_cannot_form_a_cycle_and_both_rules_agree():
    """n = 1: der einzige mögliche zweite Besuch wäre direkt nach dem ersten und ist verboten; Pricing, Schranke und Aufzählung sind für beide Regeln gleich."""
    inst = _instanz([(0, 0), (3, 4)], [2], [0], [100])
    dual = (0, 20)
    assert A.price(inst, dual, 1, eps=0, neg=0).routen == A.price(inst, dual, 1, eps=0, neg=0).routen == [(14 - 20, (1,))]
    assert A.aufzaehlung(inst, dual, False, 0) == A.aufzaehlung(inst, dual, True, 0) == (-6, (1,), 1, 0, 1)
    lauf = M.spaltenerzeugung(inst, 1, exakt=True, max_neu=1)
    assert lauf["schranke"] == 14 and lauf["spalten"] == [(1,)]


def test_exactly_two_customers_allow_the_smallest_cycle():
    """n = 2: der kleinste Fall mit Kreis (1, 2, 1); der Zweig „n < 2“ und die Gedächtnisregel dürfen ihn nicht verhindern.

    Handrechnung (Kapazität 3, Last je Kunde 1, Dualpreise 10 und 4, Entfernungen d(0,1) = 1, d(0,2) = 2, d(1,2) = 1): Route (1, 2, 1) kostet 1 + 1 + 1 + 1 = 4, Dualpreise 10 + 4 + 10 = 24,
    reduzierte Kosten 4 − 24 = −20; elementar ist (1, 2) mit 1 + 1 + 2 = 4 − 14 = −10 die beste (Gleichstand mit (2, 1): kleinere Folge zuerst)."""
    inst = _instanz([(0, 0), (1, 0), (2, 0)], [1, 1], [0, 0], [100, 100], kapazitaet=3)
    dual = (0, 10, 4)
    assert A.price(inst, dual, 1, eps=0, neg=0).routen[0] == (4 - 24, (1, 2, 1))
    assert A.price(inst, dual, 2, eps=0, neg=0).routen[0] == (4 - 14, (1, 2))
    # zulässige Routen ohne direkte Wiederholung: (1), (2), (1,2), (2,1), (1,2,1), (2,1,2) = 6, davon 2 mit Kreis; negative reduzierte Kosten: alle außer (2) = 5
    assert A.aufzaehlung(inst, dual, False, 0) == (-20, (1, 2, 1), 6, 2, 5)
    assert A.aufzaehlung(inst, dual, True, 0) == (-10, (1, 2), 4, 0, 3)


def test_a_customer_whose_load_equals_the_capacity_cannot_be_visited_twice():
    """Last gleich Kapazität: ein zweiter Besuch passt nie; Kreise sind unmöglich, die Schranke ist die elementare."""
    inst = _instanz([(0, 0), (1, 0), (2, 0), (0, 3)], [5, 5, 5], [0, 0, 0], [100, 100, 100], kapazitaet=5)
    dual = (0, 9, 9, 9)
    assert not any(A.hat_kreis(r) for r in A.alle_routen(inst, False, 0))
    assert M.spaltenerzeugung(inst, 1, exakt=True, max_neu=1)["schranke"] == M.spaltenerzeugung(inst, 3, exakt=True, max_neu=1)["schranke"]
    assert A.price(inst, dual, 1, eps=0, neg=0).routen == A.price(inst, dual, 3, eps=0, neg=0).routen


def test_capacity_exactly_equal_to_the_load_of_two_visits_is_allowed_but_one_more_unit_is_not():
    inst = _instanz([(0, 0), (1, 0), (2, 0)], [3, 2], [0, 0], [100, 100], kapazitaet=10)        # Kreis 1, 2, 1, 2: Last 3 + 2 + 3 + 2 = 10
    assert (1, 2, 1, 2) in A.alle_routen(inst, False, 0)
    assert (1, 2, 1, 2) not in A.alle_routen(replace(inst, kapazitaet=9), False, 0)


def test_windows_too_narrow_for_a_second_visit_leave_no_cycle_and_no_gap():
    """Fenster ohne Spielraum (Breite 0): die zweite Ankunft liegt nach dem Fensterende; Kreise sind unmöglich, Lücke 0 (wie bei sehr engen Fenstern in den Messreihen)."""
    punkte = [(0, 0), (4, 0), (0, 4), (4, 4)]
    inst = _instanz(punkte, [1, 1, 1], [4, 4, 8], [4, 4, 8], kapazitaet=10, horizont=50)          # Fenster [d(0, i), d(0, i)]: nur die erste Fahrt vom Depot passt
    lauf1, laufe = M.spaltenerzeugung(inst, 1, exakt=True, max_neu=1), M.spaltenerzeugung(inst, 3, exakt=True, max_neu=1)
    assert not any(A.hat_kreis(r) for r in A.alle_routen(inst, False, 0))
    assert lauf1["schranke"] == laufe["schranke"] and E.luecke(laufe["schranke"], lauf1["schranke"]) == 0


def test_two_customers_at_the_same_place_have_distance_zero_and_still_obey_the_rules():
    inst = _instanz([(0, 0), (5, 5), (5, 5)], [1, 1], [0, 0], [100, 100])
    assert inst.dist[1][2] == 0
    dual = (0, 12, 12)
    assert A.price(inst, dual, 1, eps=0, neg=0).bester_wert == A.aufzaehlung(inst, dual, False, 0)[0]
    assert A.price(inst, dual, 2, eps=0, neg=0).bester_wert == A.aufzaehlung(inst, dual, True, 0)[0]


def test_ties_between_equal_routes_are_resolved_by_the_smaller_visit_sequence():
    """Zwei Kunden am selben Ort mit gleichem Dualpreis: die Routen (1,) und (2,) haben gleiche reduzierte Kosten; die kleinere Besuchsfolge kommt zuerst."""
    inst = _instanz([(0, 0), (5, 5), (5, 5)], [1, 1], [0, 0], [100, 100])
    routen = A.price(inst, (0, 30, 30), 2, eps=0, neg=0).routen
    gleich = [r for rc, r in routen if rc == routen[0][0]]
    assert gleich == sorted(gleich) and routen[0][1] == min(gleich)


def test_zero_dual_prices_give_no_route_and_an_empty_result():
    hand = S.handbeispiel()
    res = A.price(hand, (0,) * 8, 1, eps=0, neg=0)
    assert res.routen == [] and res.bester_wert == 0 and A.aufzaehlung(hand, (0,) * 8, False, 0)[:2] == (0, ())


def test_column_generation_on_a_hand_example_ends_with_no_route_of_negative_cost():
    hand = S.handbeispiel()
    lauf = M.spaltenerzeugung(hand, 1, exakt=True, max_neu=1)
    dual = lauf["runden"][-1]["dual"]
    assert A.price(hand, dual, 1, eps=0, neg=0).routen == []


def test_the_horizon_limit_is_inclusive_and_the_service_time_counts_on_the_way_back():
    inst = _instanz([(0, 0), (3, 0)], [1], [0], [100], horizont=3 + 2 + 3)                  # Ankunft 3, Bedienzeit 2, zurück 3: genau 8 = Horizont
    assert A.alle_routen(inst, False, 0) == [(1,)]
    assert A.alle_routen(replace(inst, horizont=7), False, 0) == []


def test_the_live_run_survives_the_smallest_instances_and_unusual_seeds():
    for n in (5, 6):
        for seed in (0, 999999):
            z = E.live_lauf(n, 20, seed)
            assert z["fehler"] is None and z["k1"]["spalten"] >= 1
    z = E.live_lauf(5, 200, 1)
    assert z["fehler"] is None and (z["luecke"] is None or z["luecke"] >= -1e-9)


def test_gap_helper_handles_missing_and_zero_values():
    assert E.luecke(None, 3.0) is None and E.luecke(3.0, None) is None and E.luecke(0, 0) is None
    assert E.luecke(30, 30) == 0 and E.luecke(30, 27) == pytest.approx(0.1)
