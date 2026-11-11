"""Verdikte an von Hand gesetzten Werten (DEMO-PLAYBOOK §12): jede Schwelle der Art und jede Zahl im Text steht hier.

Ein Verdikt ist eine reine Funktion (Art, Text) und bekommt Zeilen, nicht Zufalls-Seeds. Zahlen im Text sind mit Dezimalkomma und geschütztem Leerzeichen als Tausendertrenner formatiert."""

from fractions import Fraction

import kip_evaluation as E

N = E.NBSP


def test_formats_use_decimal_comma_thousands_space_and_true_minus():
    assert E.fmt_int(1234567) == f"1{N}234{N}567" and E.fmt_int(-18) == "−18"
    assert E.fmt_dec(5.8333, 1) == "5,8" and E.fmt_dec(-0.25, 2) == "−0,25" and E.fmt_dec(12345.6, 1) == f"12{N}345,6"
    assert E.fmt_pct(0.0778, 2) == f"7,78{N}%"
    assert E.fmt_wert(Fraction(83, 3)) == "83/3 (27,67)" and E.fmt_wert(Fraction(-14, 3)) == "−14/3 (−4,67)" and E.fmt_wert(Fraction(30, 1)) == "30" and E.fmt_wert(-18) == "−18" and E.fmt_wert(2.5) == "2,50"
    assert E.weg_text((7, 6, 7, 6)) == "7 → 6 → 7 → 6" and "kein Weg" in E.weg_text(())
    assert E.doppelt_text((7, 6, 7, 6)) == "Kunden 6 und 7 mehrfach" and E.doppelt_text((5, 3, 5)) == "Kunde 5 mehrfach" and E.doppelt_text((2, 7, 6)) == ""


def _z(wert, weg):
    return {"bester_wert": wert, "weg": weg}


def test_kreis_verdict_success_when_the_cycle_over_customer_7_beats_the_best_elementary_route():
    kind, text = E.verdict_kreis_hand(_z(-18, (7, 6, 7, 6)), _z(-10, (2, 7, 6)), (-18, (7, 6, 7, 6)), 10)
    assert kind == "success"
    assert "reduzierte Kosten −18 (Weg 7 → 6 → 7 → 6, Kunden 6 und 7 mehrfach), elementar −10 (Weg 2 → 7 → 6)" in text
    assert "der Kreis macht den besten Weg um 8 günstiger" in text
    assert "bei Dualpreis 10 für Kunde 7 lohnt sich dieser Kreis gegenüber dem besten elementaren Weg (−10)" in text


def test_kreis_verdict_info_when_the_cycle_over_customer_7_does_not_beat_the_elementary_route_including_a_tie():
    for rc7 in (-2, -8):                       # −8 = Gleichstand mit dem besten elementaren Weg: strikt besser ist nötig
        kind, text = E.verdict_kreis_hand(_z(-14, (5, 3, 5, 1)), _z(-8, (5, 3, 1)), (rc7, (7, 6, 7, 6)), 5)
        assert kind == "info" and f"reduzierte Kosten {E.fmt_wert(rc7)}: bei Dualpreis 5 für Kunde 7 lohnt sich dieser Kreis nicht gegenüber" in text
        assert "Kunde 5 mehrfach" in text and "Kunden 6 und 7" not in text.split("Der beste Weg mit Kunde 7")[0]
    kind, text = E.verdict_kreis_hand(_z(-14, (5, 3, 5, 1)), _z(-8, (5, 3, 1)), (-10, (7, 6, 7, 6)), 6)
    assert kind == "success" and "lohnt sich dieser Kreis gegenüber dem besten elementaren Weg (−8)" in text


def test_kreis_verdict_without_any_cycle_advantage_or_without_a_feasible_double_visit():
    kind, text = E.verdict_kreis_hand(_z(-8, (5, 3, 1)), _z(-8, (5, 3, 1)), None, 10)
    assert kind == "info" and "ohne Kreis" in text and "keinen besseren Weg" in text and "Kunde 7 zweimal besucht, ist bei diesen Fenstern und dieser Last nicht zulässig" in text
    kind, text = E.verdict_kreis_hand(_z(0, ()), _z(0, ()), None, 2)
    assert kind == "info" and "kein Weg negative reduzierte Kosten" in text


def _cg(runden, schranke, mit_kreis, neue, labels):
    return {"runden": runden, "schranke": schranke, "mit_kreis": mit_kreis, "neue": neue, "labels": labels}


def test_colgen_verdict_names_bounds_gap_cycle_share_and_the_check():
    k1, el = _cg(8, Fraction(83, 3), 4, [0] * 7, 416), _cg(7, 30, 0, [0] * 6, 326)
    kind, text = E.verdict_colgen_hand(k1, el, {"wert": Fraction(83, 3), "spalten": 89}, {"wert": 30, "spalten": 79})
    assert kind == "warning"
    assert "nach 8 Runden bei der Schranke 83/3 (27,67), elementar nach 7 Runden bei 30" in text
    assert "4 von 7 neuen Spalten enthalten einen Kreis" in text and "416 mit erlaubten Kreisen, 326 elementar" in text
    assert "über alle 89 bzw. 79 zulässigen Routen): gleiche Schranken" in text and f"liegt 7,78{N}% unter der elementaren" in text


def test_colgen_verdict_equal_bounds_and_a_failed_check():
    kind, text = E.verdict_colgen_hand(_cg(5, 30, 0, [0] * 4, 100), _cg(5, 30, 0, [0] * 4, 120), {"wert": 30, "spalten": 10}, {"wert": 30, "spalten": 10})
    assert kind == "info" and "Die beiden Schranken sind gleich." in text
    kind, text = E.verdict_colgen_hand(_cg(5, 30, 0, [0] * 4, 100), _cg(5, 30, 0, [0] * 4, 120), {"wert": 29, "spalten": 10}, {"wert": 30, "spalten": 10})
    assert "ABWEICHUNG" in text


def _live(mit, spalten, s1, se, luecke, abgebrochen=False, vgl=1234):
    return {"n": 15, "breite": 100, "seed": 0, "luecke": luecke,
            "k1": {"mit_kreis": mit, "spalten": spalten, "schranke": s1}, "elem": {"abgebrochen": abgebrochen, "schranke": se, "vergleiche": vgl, "labels": 99}}


def test_live_verdict_gap_equal_bounds_and_aborted_elementary_run():
    kind, text = E.verdict_live(_live(55, 76, 411.46, 440.88, 0.0667))
    assert kind == "warning" and f"55 von 76 neuen Spalten ({E.fmt_pct(55 / 76)}) enthalten einen Kreis (n = 15, Breite 100, Zufalls-Seed 0)" in text
    assert "Schranke mit erlaubten Kreisen 411,46, elementar 440,88" in text and f"liegt 6,67{N}% unter der elementaren" in text
    kind, text = E.verdict_live(_live(3, 70, 500.0, 500.0, 0.0))
    assert kind == "info" and "Lücke 0" in text and "obwohl Kreise erlaubt waren" in text
    kind, text = E.verdict_live(_live(40, 80, 500.0, None, None, abgebrochen=True, vgl=30_000_004))
    assert kind == "warning" and f"30{N}000{N}004 Dominanztests" in text and "keine elementare Schranke und keine Lücke" in text
    kind, text = E.verdict_live(_live(0, 0, 500.0, 500.0, 0.0))
    assert "0 von 0 neuen Spalten enthalten einen Kreis" in text


def test_cycle_length_verdict():
    fest = {"mit_kreis": 865, "kuerzeste": {"2": 845, "3": 20, "4+": 0}, "instanzen": 6}
    live = {"mit_kreis": 55, "kuerzeste": {"2": 54, "3": 1, "4+": 0}}
    kind, text = E.verdict_kreislaengen(live, fest, 100)
    assert kind == "success" and "von 55 Kreis-Spalten 54 als kürzesten Kreis zwei Kanten (i, j, i), 1 drei Kanten und 0 vier oder mehr" in text
    assert f"von 865 Kreis-Spalten 845 ({E.fmt_pct(845 / 865)}) als kürzesten Kreis zwei Kanten" in text and "(n = 30, Breite 100, 6 Instanzen)" in text
    kind, text = E.verdict_kreislaengen({"mit_kreis": 0, "kuerzeste": {"2": 0, "3": 0, "4+": 0}}, fest, 100)
    assert kind == "info" and "keine neue Spalte einen Kreis" in text
    kind, text = E.verdict_kreislaengen({"mit_kreis": 0, "kuerzeste": {"2": 0, "3": 0, "4+": 0}}, {"mit_kreis": 0, "kuerzeste": {"2": 0, "3": 0, "4+": 0}, "instanzen": 6}, 20)
    assert "In der festen Messreihe (Breite 20) gibt es keine Kreis-Spalten" in text


def _kz(breite, neue, kreis, ende, ende_kreis):
    return {"breite": breite, "instanzen": 6, "neue_spalten": neue, "mit_kreis": kreis, "anteil_neue": kreis / neue, "ende_spalten": ende, "ende_kreis": ende_kreis, "anteil_ende": ende_kreis / ende}


def test_bands_verdict_for_the_share_of_cycle_columns_grows_or_does_not():
    wachsend = [_kz(40, 1108, 62, 105, 9), _kz(100, 1206, 865, 142, 79), _kz(200, 1320, 1175, 149, 119)]
    kind, text = E.verdict_kreise_baender(wachsend)
    assert kind == "success" and f"Breite 40: 5,6{N}% der neuen Spalten (62 von 1{N}108), 8,6{N}% der Spalten der Endlösung (9 von 105)" in text
    assert f"Breite 200: 89,0{N}% der neuen Spalten (1{N}175 von 1{N}320)" in text and "Der Anteil wächst mit der Breite." in text and "6 Instanzen je Breite" in text
    kind, text = E.verdict_kreise_baender([_kz(40, 100, 50, 10, 5), _kz(100, 100, 40, 10, 5)])
    assert kind == "info" and "wächst nicht mit jeder Breite" in text


def test_bands_verdict_for_the_gap_lists_every_cell_and_names_the_scope():
    zeilen = [{"n": 10, "breite": 40, "mittel": 0.0072}, {"n": 15, "breite": 40, "mittel": 0.0062}, {"n": 10, "breite": 100, "mittel": 0.0545}]
    kind, text = E.verdict_luecke_baender(zeilen)
    assert kind == "info"
    assert f"Breite 40: n = 10: 0,72{N}%, n = 15: 0,62{N}%; Breite 100: n = 10: 5,45{N}%" in text and "nur für diese Breiten und Größen" in text
