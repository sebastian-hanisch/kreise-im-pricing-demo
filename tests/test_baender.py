"""Feste Messreihen (data/*.json): Aufbau, Quellenangaben, Vergleich mit der Messung vor dem Bau und Stichproben, die mit dem Kern dieser Demo nachgerechnet werden.

Die JSON-Dateien hat `tools/baender_erzeugen.py` mit dem Kern dieser Demo gerechnet. Die Stichproben hier rechnen Zellen noch einmal: Schranken müssen auf 1e-6 (relativ) stimmen (der Wert der
Schranke hängt nicht vom Weg der Spaltenerzeugung ab); Zählungen von Spalten hängen vom Master-Löser ab und werden nur in Bändern geprüft (DEMO-PLAYBOOK §4: Plattformabhängiges nie exakt)."""

import pytest

import kip_algorithm as A
import kip_baender as B
import kip_master as M
import kip_scenario as S


def test_every_cell_names_its_source_and_every_row_has_its_fields():
    for z in B._lade("baender_kreise.json")["zellen"]:
        assert "neu gerechnet" in z["quelle"] and len(z["zeilen"]) == 6 and [r["seed"] for r in z["zeilen"]] == list(range(6))
        for r in z["zeilen"]:
            assert {"neue_spalten", "mit_kreis", "schranke", "ende_spalten", "ende_kreis", "ende_menge", "ende_menge_kreis", "kuerzester_kreis", "wiederholungen"} <= set(r)
            assert r["mit_kreis"] <= r["neue_spalten"] and r["ende_kreis"] <= r["ende_spalten"] and sum(r["kuerzester_kreis"].values()) == r["mit_kreis"] and sum(r["wiederholungen"].values()) == r["mit_kreis"]
    for z in B.luecke_zellen():
        assert z["quelle"] and z["bezug"] in B.BEZUEGE and (z["neu_gerechnet"] == ("zeilen" in z))
        for r in z.get("zeilen", []):
            assert {"seed", "schranke_k1", "schranke_ref", "abgebrochen"} <= set(r) and (r["schranke_ref"] is None) == r["abgebrochen"]
            assert r["abgebrochen"] or r["schranke_k1"] <= r["schranke_ref"] + 1e-6          # k = 1 liegt nie über dem Bezug


def test_the_cells_cover_the_documented_grid():
    ids = {z["id"] for z in B.luecke_zellen()}
    assert {f"elementar_n{n}_b{b}" for n in (10, 15, 20, 25, 30) for b in (40, 100)} <= ids and {"k8_zufall", "k8_cluster", "k8_lang"} <= ids
    assert len([z for z in B.luecke_zellen() if z["bezug"] == "k = 16"]) == 8 and B.kreise_breiten() == [40, 100, 200]
    assert all(len(z["zeilen"]) == 6 for z in B.luecke_zellen() if z["bezug"] == "elementar") and all(len(z["zeilen"]) == 5 for z in B.luecke_zellen() if z["bezug"] == "k = 8")


def test_every_recomputed_bound_agrees_with_the_measurement_before_the_build():
    v = B.vormessung_vergleiche()
    assert v["abweichend"] == 0 and v["verglichen"] == 147
    for z in B._lade("baender_kreise.json")["zellen"]:
        assert z["vormessung"]["gleich"] is True           # Summen der Spalten mit Kreis gleich den Logdateien der Vormessung


def test_gap_summaries_and_the_gap_of_a_single_row():
    z = B.luecke_zelle("elementar_n10_b100")
    kz = B.luecke_kennzahlen(z)
    luecken = [B.luecke_zeile(r) for r in z["zeilen"]]
    assert kz["mittel"] == pytest.approx(sum(luecken) / 6) and kz["maximum"] == max(luecken) and kz["fertig"] == 6 and kz["abgebrochen"] == 0
    r = z["zeilen"][0]
    assert B.luecke_zeile(r) == pytest.approx((r["schranke_ref"] - r["schranke_k1"]) / r["schranke_ref"])
    abgebrochen = {**r, "abgebrochen": True, "schranke_ref": None}
    assert B.luecke_zeile(abgebrochen) is None


def test_cycle_sums_are_the_sums_over_the_instances():
    for b in B.kreise_breiten():
        z, s = B.kreise_zelle(b), B.kreise_summe(b)
        assert s["neue_spalten"] == sum(r["neue_spalten"] for r in z["zeilen"]) and s["mit_kreis"] == sum(r["mit_kreis"] for r in z["zeilen"])
        assert sum(s["kuerzeste"].values()) == s["mit_kreis"] and sum(s["wiederholungen"].values()) == s["mit_kreis"]
        assert s["anteil_neue"] == s["mit_kreis"] / s["neue_spalten"]


def test_sample_of_the_cycle_series_recomputed_with_the_kernel():
    """Breite 100 und Breite 40, je eine Instanz: Schranke exakt (relativ 1e-6), Zahl neuer Spalten und der Spalten mit Kreis im Band ±20 % der gespeicherten Werte."""
    for breite, seed in ((100, 3), (40, 3)):
        zeile = next(r for r in B.kreise_zelle(breite)["zeilen"] if r["seed"] == seed)
        inst = S.make_instance(30, seed, breite)
        lauf = M.spaltenerzeugung(inst, 1)
        neue = M.neue_spalten(lauf, 30)
        assert lauf["schranke"] == pytest.approx(zeile["schranke"], rel=1e-6)
        assert zeile["neue_spalten"] * 0.8 <= len(neue) <= zeile["neue_spalten"] * 1.2
        kreis = sum(1 for r in neue if A.hat_kreis(r))
        assert zeile["mit_kreis"] * 0.8 - 2 <= kreis <= zeile["mit_kreis"] * 1.2 + 2


def test_sample_of_the_gap_series_recomputed_with_the_kernel():
    """n = 15, Breite 100, Seed 2 und n = 20, Breite 40, Seed 4: beide Schranken stimmen mit den gespeicherten überein; die Lücke ist nicht negativ."""
    for zid, seed in (("elementar_n15_b100", 2), ("elementar_n20_b40", 4)):
        z = B.luecke_zelle(zid)
        zeile = next(r for r in z["zeilen"] if r["seed"] == seed)
        inst = S.make_instance(z["n"], seed, z["breite"])
        k1 = M.spaltenerzeugung(inst, 1)["schranke"]
        el = M.spaltenerzeugung(inst, inst.n)["schranke"]
        assert k1 == pytest.approx(zeile["schranke_k1"], rel=1e-6) and el == pytest.approx(zeile["schranke_ref"], rel=1e-6) and k1 <= el + 1e-7


def test_sample_of_the_k8_series_recomputed_with_the_kernel():
    z = B.luecke_zelle("k8_lang")
    zeile = next(r for r in z["zeilen"] if r["seed"] == 1)
    inst = S.make_instance(30, 1, 60, horizont=500.0, kapazitaet=120)
    assert M.spaltenerzeugung(inst, 1)["schranke"] == pytest.approx(zeile["schranke_k1"], rel=1e-6)
    assert M.spaltenerzeugung(inst, 8)["schranke"] == pytest.approx(zeile["schranke_ref"], rel=1e-6)


def test_the_k16_rows_are_marked_as_not_recomputed_and_carry_the_values_of_the_summary_file():
    zs = [z for z in B.luecke_zellen() if z["bezug"] == "k = 16"]
    assert all(z["neu_gerechnet"] is False and "nicht neu gerechnet" in z["quelle"] and "zeilen" not in z for z in zs)
    tab = {(r["typ"], r["n"], r["breite"]): r for r in B.luecke_k16_tabelle()}
    assert tab[("zufall", 50, 100)]["mittel"] == pytest.approx(0.03227) and tab[("cluster", 100, 20)]["null_in"] == 12 and tab[("zufall", 100, 40)]["instanzen"] == 12


def test_the_n30_comparison_with_the_earlier_measurement():
    v = B.luecke_n30_vergleich()
    assert (v["instanzen"], v["fertig_vor"], v["abgebrochen_vor"], v["fertig_hier"]) == (6, 3, 3, 6)
    assert v["mittel_vor"] == pytest.approx(0.0482, abs=5e-5) and v["mittel_hier"] == pytest.approx(0.0333, abs=5e-5)
