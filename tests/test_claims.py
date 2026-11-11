"""Jede Zahl der README (Abschnitt „Befunde“) wird hier nachgerechnet, mit denselben Auswertungsfunktionen wie in der App (DEMO-PLAYBOOK §4).

* Handbeispiel: exakte Zählungen und Brüche des Kerns (ganze Zahlen und `Fraction`; Anteile und Quotienten als Rechnung).
* Zufallsinstanzen: die Bänder stammen aus den JSON-Dateien in data/ (mit dem Kern dieser Demo gerechnet, `tools/baender_erzeugen.py`); `tests/test_baender.py` rechnet Stichproben nach.
  Die Zeilen mit Bezug k = 16 sind nur aus der Auswertungsdatei der Messung vor dem Bau übernommen und nicht neu gerechnet.
* Zeiten stehen nirgends in der README und nirgends hier.
Wo eine Zahl auf dem Master-Löser beruht (Zahl der Spalten, Runden), steht in der README, dass sie auf einem Windows-Rechner gerechnet ist; die Schranken sind davon unabhängig."""

import random
from fractions import Fraction

import pytest

import kip_algorithm as A
import kip_baender as B
import kip_evaluation as E
import kip_scenario as S

HAND = S.handbeispiel()


def _proz(x):
    return round(100 * x, 1)


def _proz2(x):
    return round(float(100 * x), 2)


# --- Handbeispiel ---------------------------------------------------------------------------------------------------------------------------

def test_hand_example_round_one_pricing_with_cycles_and_elementary():
    kreis, ze = E.hand_kreis(10)["k1"], E.hand_kreis(10)["elem"]
    assert (kreis["erzeugt"], kreis["dominiert"], kreis["erzeugt"] - kreis["dominiert"]) == (62, 32, 30)
    assert kreis["weg"] == (7, 6, 7, 6) and kreis["bester_wert"] == (5 + 2 + 2 + 2 + 3) - (10 + 6 + 10 + 6) == -18
    assert ze["erzeugt"] == 56 and ze["weg"] == (2, 7, 6) and ze["bester_wert"] == (3 + 4 + 2 + 3) - (6 + 10 + 6) == -10
    assert kreis["bester_wert"] - ze["bester_wert"] == -8
    assert kreis["fehler"] is None and ze["fehler"] is None


def test_hand_example_enumeration_counts():
    kreis, ze = E.hand_kreis(10)["k1"], E.hand_kreis(10)["elem"]
    assert (kreis["aufz_wege"], kreis["aufz_kreis"], kreis["aufz_negativ"], ze["aufz_wege"], ze["aufz_kreis"]) == (89, 10, 68, 79, 0)
    assert ze["aufz_negativ"] == 58                                                  # elementar: 58 der 79 Routen haben negative reduzierte Kosten (App-Text)
    mit_kreis = [r for r in A.alle_routen(HAND, False, 0) if A.hat_kreis(r)]
    assert len(mit_kreis) == 10 and all(A.route_kosten(HAND, S.hand_dualpreise(10), r) < 0 for r in mit_kreis)


def test_hand_example_dual_price_of_customer_7_from_2_to_14():
    wege = {}
    for d7 in range(2, 15):
        z = E.hand_kreis(d7)
        wege[d7] = (z["k1"]["weg"], z["k1"]["bester_wert"], z["elem"]["bester_wert"], z["kunde7"])
        assert A.hat_kreis(z["k1"]["weg"]), d7
    assert all(wege[d][0] == (5, 3, 5, 1) and wege[d][1] == -14 for d in range(2, 9))
    assert all(wege[d][0] == (7, 6, 7, 6) and wege[d][1] == 2 - 2 * d for d in range(9, 15))
    assert wege[8][3][0] == -14                                              # bei 8 gleichauf mit (5, 3, 5, 1)
    lohnt = {d: wege[d][3][0] < wege[d][2] for d in wege}
    assert [d for d in wege if not lohnt[d]] == [2, 3, 4, 5] and [d for d in wege if lohnt[d]] == list(range(6, 15))
    assert wege[5][3][0] == wege[5][2] == -8                                  # Gleichstand bei Dualpreis 5: strikt besser ist nötig
    assert all(wege[d][3][0] == (14 - (2 * d + 12)) for d in wege)             # 7 → 6 → 7 → 6: Weglänge 14, Dualpreise 2d + 12


def test_hand_example_first_round_cycle_has_double_the_reduced_cost():
    dual = S.hand_dualpreise(10)
    assert A.route_kosten(HAND, dual, (7, 6)) == -6 and A.route_kosten(HAND, dual, (7, 6, 7)) == -12
    assert A.route_kosten(HAND, dual, (7, 6, 7)) == 2 * (HAND.dist[7][6] - HAND.dist[0][7] - HAND.dist[0][6]) == 2 * (2 - 5 - 3)


def test_hand_example_column_generation():
    k1, el = E.hand_spaltenerzeugung(False), E.hand_spaltenerzeugung(True)
    assert [r["wert"] for r in k1["lauf"]["runden"]] == [50, 41, 33, 33, 32, 29, 28, Fraction(83, 3)] and k1["runden"] == 8
    assert (len(k1["neue"]), k1["mit_kreis"], k1["labels"]) == (7, 4, 416) and all(A.kuerzester_kreis(r) == 2 for r in k1["neue"] if A.hat_kreis(r))
    assert [(r, x) for r, x in k1["ende"]] == [((7, 6, 7, 6), Fraction(1, 2)), ((2, 1), 1), ((3, 4), Fraction(2, 3)), ((5, 3, 5), Fraction(1, 3)), ((5, 4), Fraction(1, 3))]
    assert (el["schranke"], el["runden"], el["labels"]) == (30, 7, 326)
    assert E.hand_gegenprobe(False)["wert"] == Fraction(83, 3) and E.hand_gegenprobe(True)["wert"] == 30
    assert _proz2(E.luecke(30, Fraction(83, 3))) == 7.78


def test_hand_example_half_cycle_trip():
    halbe = E.hand_halbe_kreisfahrt(E.hand_spaltenerzeugung(False), HAND)
    assert halbe["route"] == (7, 6, 7, 6) and halbe["kosten"] == 14 and halbe["anteilig"] == Fraction(14, 2) == 7 and (halbe["elementar_route"], halbe["elementar_kosten"]) == ((7, 6), 10)


# --- Orakel der Vorabmessung (180 Fälle) ---------------------------------------------------------------------------------------------------

def test_180_cases_with_7_customers_k1_is_below_the_elementary_optimum_in_102_and_never_above():
    unter = ueber = faelle = 0
    for seed in range(60):
        for breite in (30, 80, 200):
            inst = S.make_instance(7, seed, breite)
            rng = random.Random(1000 + seed)
            dual = [0.0] + [rng.uniform(20, 70) for _ in range(inst.n)]
            elementar = A.price(inst, dual, inst.n, max_routes=1).bester_wert
            kreise = A.price(inst, dual, 1, max_routes=1).bester_wert
            faelle += 1
            unter += kreise < elementar - 1e-6
            ueber += kreise > elementar + 1e-6
    assert (faelle, unter, ueber) == (180, 102, 0) and _proz(unter / faelle) == 56.7


# --- Bänder (a): Anteil der Spalten mit Kreis ------------------------------------------------------------------------------------------------

def test_share_of_cycle_columns_by_width():
    t = {z["breite"]: z for z in B.kreise_tabelle()}
    assert [(b, t[b]["instanzen"], t[b]["mit_kreis"], t[b]["neue_spalten"]) for b in (40, 100, 200)] == [(40, 6, 62, 1108), (100, 6, 865, 1206), (200, 6, 1175, 1320)]
    assert [_proz(t[b]["anteil_neue"]) for b in (40, 100, 200)] == [5.6, 71.7, 89.0]
    assert [(t[b]["ende_kreis"], t[b]["ende_spalten"]) for b in (40, 100, 200)] == [(9, 105), (79, 142), (119, 149)]
    assert [_proz(t[b]["anteil_ende"]) for b in (40, 100, 200)] == [8.6, 55.6, 79.9]
    assert [_proz(t[b]["anteil_menge"]) for b in (40, 100, 200)] == [4.9, 46.3, 69.0]


def test_shortest_cycle_and_repetitions_per_cycle_column():
    t = {z["breite"]: z for z in B.kreise_tabelle()}
    assert [(t[b]["kuerzeste"]["2"], t[b]["kuerzeste"]["3"], t[b]["kuerzeste"]["4+"]) for b in (40, 100, 200)] == [(62, 0, 0), (845, 20, 0), (1104, 64, 7)]
    assert _proz(845 / 865) == 97.7 and _proz(1104 / 1175) == 94.0
    assert list(t[100]["wiederholungen"].items()) == [(1, 519), (2, 240), (3, 82), (4, 16), (5, 6), (6, 2)] and sum(t[100]["wiederholungen"].values()) == 865
    assert round(t[100]["laenge_neue"], 2) == 4.89 and round(t[100]["laenge_kreis"], 2) == 5.24


def test_the_default_live_instance():
    z = E.live_lauf(15, 100, 0)
    assert (z["k1"]["mit_kreis"], z["k1"]["spalten"]) == (55, 76) and z["elem"]["abgebrochen"] is False and z["fehler"] is None
    assert round(z["k1"]["schranke"], 2) == 411.46 and round(z["elem"]["schranke"], 2) == 440.88 and _proz2(z["luecke"]) == 6.67


# --- Bänder (b): Lücke zur elementaren Schranke -------------------------------------------------------------------------------------------

LUECKE = {  # (n, Breite): (Mittel %, Maximum %, Instanzen mit Lücke 0 von 6)
    (10, 40): (0.72, 4.33, 5), (15, 40): (0.62, 2.71, 3), (20, 40): (0.51, 2.56, 4), (25, 40): (0.74, 1.47, 0), (30, 40): (0.24, 0.72, 2),
    (10, 100): (5.45, 13.91, 1), (15, 100): (4.47, 6.89, 0), (20, 100): (4.42, 7.40, 0), (25, 100): (3.98, 4.57, 0), (30, 100): (3.33, 6.80, 0),
}


def test_gap_to_the_elementary_bound_by_n_and_width():
    tab = {(z["n"], z["breite"]): z for z in B.luecke_elementar_tabelle()}
    assert set(tab) == set(LUECKE)
    for schluessel, (mittel, maximum, null) in LUECKE.items():
        z = tab[schluessel]
        assert (z["instanzen"], z["fertig"], z["abgebrochen"]) == (6, 6, 0), schluessel
        assert (_proz2(z["mittel"]), _proz2(z["maximum"]), z["null_in"]) == (mittel, maximum, null), schluessel


def test_the_gap_range_named_in_the_readme():
    mittel = [_proz2(z["mittel"]) for z in B.luecke_elementar_tabelle()]
    assert min(mittel) == 0.24 and max(mittel) == 5.45
    assert min(_proz2(z["mittel"]) for z in B.luecke_elementar_tabelle() if z["breite"] == 100) == 3.33
    assert E.luecke(30, Fraction(83, 3)) > max(z["mittel"] for z in B.luecke_elementar_tabelle())          # die Lücke des Handbeispiels liegt über jedem Mittel der Messreihen
    assert [_proz2(z["mittel"]) for z in B.luecke_elementar_tabelle() if z["breite"] == 40] == [0.72, 0.62, 0.51, 0.74, 0.24] and max(z["mittel"] for z in B.luecke_elementar_tabelle() if z["breite"] == 40) < 0.0075


def test_n30_width_100_all_six_elementary_runs_finish_and_the_three_earlier_ones_had_the_larger_gaps():
    v = B.luecke_n30_vergleich()
    assert (v["instanzen"], v["fertig_vor"], v["abgebrochen_vor"], v["fertig_hier"]) == (6, 3, 3, 6) and (_proz2(v["mittel_vor"]), _proz2(v["mittel_hier"])) == (4.82, 3.33)
    assert B.grenze_vergleiche() == 600_000_000


def test_labels_of_the_whole_column_generation_at_n_30():
    tab = {(z["n"], z["breite"]): z for z in B.luecke_elementar_tabelle()}
    assert (tab[(30, 40)]["labels_k1"], tab[(30, 40)]["labels_ref"]) == (16938.5, 40175.0)
    assert (tab[(30, 100)]["labels_k1"], tab[(30, 100)]["labels_ref"]) == (57329.5, 186957.0)
    assert all(z["labels_k1"] < z["labels_ref"] for z in tab.values())


def test_gap_to_k8_for_three_instance_types():
    tab = {z["typ"]: z for z in B.luecke_k8_tabelle()}
    assert [(typ, tab[typ]["instanzen"], _proz2(tab[typ]["mittel"]), _proz2(tab[typ]["maximum"])) for typ in ("zufall", "cluster", "lang")] == [
        ("zufall", 5, 3.56, 6.80), ("cluster", 5, 4.37, 7.12), ("lang", 5, 2.24, 5.71)]
    assert [tab[t]["null_in"] for t in ("zufall", "cluster", "lang")] == [0, 0, 1]


def test_gap_to_k16_from_the_summary_file_not_recomputed():
    tab = {(z["typ"], z["n"], z["breite"]): z for z in B.luecke_k16_tabelle()}
    erwartet = {("cluster", 50, 100): (2.518, 3.651), ("zufall", 50, 100): (3.227, 4.811), ("cluster", 50, 40): (0.845, 2.378), ("zufall", 50, 40): (1.191, 4.293),
                ("cluster", 100, 40): (0.762, 1.405), ("zufall", 100, 40): (0.879, 1.528), ("cluster", 100, 20): (0.0, 0.0), ("zufall", 100, 20): (0.0, 0.0)}      # drei Stellen wie in der Auswertungsdatei
    for schluessel, (mittel, maximum) in erwartet.items():
        assert (round(100 * tab[schluessel]["mittel"], 3), round(100 * tab[schluessel]["maximum"], 3)) == (mittel, maximum), schluessel
        assert tab[schluessel]["instanzen"] == 12
    assert tab[("cluster", 100, 20)]["null_in"] == tab[("zufall", 100, 20)]["null_in"] == 12


def test_all_recomputed_bounds_agree_with_the_measurement_before_the_build():
    assert B.vormessung_vergleiche() == {"verglichen": 147, "abweichend": 0}
    assert [z["vormessung"]["gleich"] for z in B._lade("baender_kreise.json")["zellen"]] == [True, True, True]
