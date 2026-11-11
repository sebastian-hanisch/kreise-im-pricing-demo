"""End-to-end-Rauchtest mit Streamlits AppTest: lädt app.py mit den Standardeinstellungen, klickt jeden Beispielszenario-Button, fährt jeden Regler an seine Grenzen, probiert jede Auswahl
und den Permalink und prüft, dass kein Python-Fehler auftritt und dass jedes Szenario die erwartete Verdikt-Zeile zeigt (DEMO-PLAYBOOK §11a Punkt 7).
Expander werden nie per Index, sondern per Titel angesprochen."""

import os

import pytest
from streamlit.testing.v1 import AppTest

import kip_baender as B
import kip_constants as C
import kip_presets as P

APP_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))  # unter Last (parallele Läufe) reichen 180 s nicht immer; Umgebungsvariable zum Anpassen
NBSP = " "


def _fresh_app() -> AppTest:
    at = AppTest.from_file(APP_PATH, default_timeout=TIMEOUT)
    at.run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _verdicts(at) -> list:
    """Alle Verdikt- und Hinweisboxen (success, info, warning) als (Art, Text)."""
    return [(kind, e.value) for kind in ("success", "info", "warning") for e in getattr(at, kind)]


def _expander(at, title):
    return next(e for e in at.expander if e.label == title)


def _regler(at, key):
    spec = P.SETTING_SPECS[key]
    if key == "h_regel":
        return at.sidebar.radio(key=key)
    if key == "l_breite":
        return at.sidebar.select_slider(key=key)
    if key == "l_seed":
        return at.sidebar.number_input(key=key)
    assert spec.choices is None
    return at.sidebar.slider(key=key)


def test_app_loads_without_exception_and_shows_the_default_verdicts():
    at = _fresh_app()
    texte = [t for _k, t in _verdicts(at)]
    assert any(t.startswith("Mit erlaubten Kreisen hat der beste Weg reduzierte Kosten −18 (Weg 7 → 6 → 7 → 6") for t in texte)
    assert any(t.startswith("Spaltenerzeugung im Handbeispiel: mit erlaubten Kreisen endet sie nach 8 Runden") for t in texte)
    assert any(t.startswith(f"55 von 76 neuen Spalten (72,4{NBSP}%)") for t in texte)
    assert not at.error


def test_every_button_click_does_not_raise():
    labels = [b.label for b in _fresh_app().button]
    assert labels, "keine Buttons gefunden"
    for index, label in enumerate(labels):
        at = _fresh_app()
        at.button[index].click().run(timeout=TIMEOUT)
        assert not at.exception, (label, [str(e) for e in at.exception])


@pytest.mark.parametrize("key", ["h_dual7", "h_runde", "l_n", "l_breite"])
def test_every_slider_at_its_min_and_max_does_not_raise(key):
    for edge in (0, -1):
        at = _fresh_app()
        spec = P.SETTING_SPECS[key]
        if spec.choices is not None:
            _regler(at, key).set_value(spec.choices[edge]).run(timeout=TIMEOUT)
        else:
            _regler(at, key).set_value(int(spec.lo if edge == 0 else spec.hi)).run(timeout=TIMEOUT)
        assert not at.exception, (key, edge, [str(e) for e in at.exception])


def test_every_choice_of_the_hand_rule_does_not_raise():
    for wert in P.SETTING_SPECS["h_regel"].choices:
        at = _fresh_app()
        at.sidebar.radio(key="h_regel").set_value(wert).run(timeout=TIMEOUT)
        assert not at.exception, (wert, [str(e) for e in at.exception])


def test_all_minima_and_all_maxima_together_do_not_raise():
    for edge in (0, -1):
        at = _fresh_app()
        for key, spec in P.SETTING_SPECS.items():
            if key == "l_seed":
                continue
            _regler(at, key).set_value(spec.choices[edge] if spec.choices is not None else int(spec.lo if edge == 0 else spec.hi))
        at.run(timeout=TIMEOUT)
        assert not at.exception, [str(e) for e in at.exception]


def test_seed_extremes_and_the_new_instance_button_do_not_raise():
    for seed in (0, C.SEED_MAX):
        at = _fresh_app()
        at.sidebar.number_input(key="l_seed").set_value(seed).run(timeout=TIMEOUT)
        assert not at.exception, seed
    at = _fresh_app()
    at.sidebar.button[-1].click().run(timeout=TIMEOUT)
    assert not at.exception and 0 <= at.session_state["l_seed"] <= C.SEED_MAX


def test_main_area_selections_do_not_raise():
    for key, werte in (("k_breite", B.kreise_breiten()), ("b_bezug", list(B.BEZUEGE))):
        for wert in werte:
            at = _fresh_app()
            at.radio(key=key).set_value(wert).run(timeout=TIMEOUT)
            assert not at.exception, (key, wert, [str(e) for e in at.exception])


def test_the_k16_selection_marks_the_rows_as_not_recomputed():
    at = _fresh_app()
    at.radio(key="b_bezug").set_value("k = 16").run(timeout=TIMEOUT)
    assert not at.exception
    assert any("nicht neu gerechnet" in w.value for w in at.warning)
    at.radio(key="b_bezug").set_value("elementar").run(timeout=TIMEOUT)
    assert any(w.value.startswith("Breite 100, n = 30: In der Messung vor dem Bau brachen 3 von 6 elementaren Läufen") for w in at.warning)


def test_permalink_sets_the_controls_and_unusable_values_fall_back_to_the_default():
    at = AppTest.from_file(APP_PATH, default_timeout=TIMEOUT)
    at.query_params["n"] = "12"
    at.query_params["w"] = "40"
    at.query_params["hr"] = C.HAND_REGELN[1]
    at.query_params["d7"] = "99"
    at.query_params["rd"] = "gibt es nicht"
    at.run(timeout=TIMEOUT)
    assert not at.exception
    assert (at.session_state["l_n"], at.session_state["l_breite"], at.session_state["h_regel"], at.session_state["h_dual7"], at.session_state["h_runde"]) == (12, 40, C.HAND_REGELN[1], C.HAND_DUAL7_MAX, C.HAND_DEFAULT_RUNDE)


# je Szenario: ein Satzanfang der erwarteten Verdikt-Zeile zu Experiment 1 (Art, Anfang oder Teilsatz) und zu Experiment 3 (Art, Teilsatz); die Zahlen kommen aus dem Kern
GRUND_HAND = ("success", "Mit erlaubten Kreisen hat der beste Weg reduzierte Kosten −18 (Weg 7 → 6 → 7 → 6, Kunden 6 und 7 mehrfach), elementar −10 (Weg 2 → 7 → 6)")
ERWARTET = {
    "Grundfall: der Kreis im Handbeispiel": (GRUND_HAND, ("warning", f"55 von 76 neuen Spalten (72,4{NBSP}%) enthalten einen Kreis (n = 15, Breite 100, Zufalls-Seed 0)")),
    "Kreis über Kunde 7 lohnt sich nicht": (("info", "reduzierte Kosten −14 (Weg 5 → 3 → 5 → 1, Kunde 5 mehrfach), elementar −8 (Weg 5 → 3 → 1)"), ("warning", "55 von 76 neuen Spalten")),
    "Enge Fenster (Breite 20)": (GRUND_HAND, ("info", f"0 von 122 neuen Spalten (0,0{NBSP}%) enthalten einen Kreis (n = 20, Breite 20, Zufalls-Seed 0)")),
    "Breite 40: Kreise ohne Lücke": (GRUND_HAND, ("info", f"59 von 172 neuen Spalten (34,3{NBSP}%) enthalten einen Kreis (n = 20, Breite 40, Zufalls-Seed 0)")),
    "Weite Fenster (Breite 200)": (GRUND_HAND, ("warning", f"56 von 80 neuen Spalten (70,0{NBSP}%) enthalten einen Kreis (n = 12, Breite 200, Zufalls-Seed 0)")),
    "Größte Einstellung (n = 20, Breite 200)": (GRUND_HAND, ("warning", f"130 von 147 neuen Spalten (88,4{NBSP}%) enthalten einen Kreis (n = 20, Breite 200, Zufalls-Seed 0)")),
}


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_each_preset_shows_the_expected_verdict_lines(name):
    at = _fresh_app()
    at.sidebar.button(key=f"preset_{name}").click().run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    (art_h, hand), (art_l, live) = ERWARTET[name]
    texte = _verdicts(at)
    assert any(k == art_h and hand in t for k, t in texte), (name, [t[:120] for _k, t in texte])
    assert any(k == art_l and live in t for k, t in texte), (name, [t[:160] for _k, t in texte])
    for key, value in C.PRESETS[name].items():
        assert at.session_state[key] == value


def test_preset_without_a_cycle_does_not_report_a_cycle_or_a_gap():
    """„Enge Fenster“: die Live-Rechnung meldet ausdrücklich Lücke 0 und keinen Kreis; Experiment 4 meldet keine Kreis-Spalte in dieser Instanz."""
    at = _fresh_app()
    at.sidebar.button(key="preset_Enge Fenster (Breite 20)").click().run(timeout=TIMEOUT)
    live = next(t for _k, t in _verdicts(at) if t.startswith("0 von 122 neuen Spalten"))
    assert "die Schranken sind gleich (Lücke 0)" in live and "unter der elementaren" not in live
    assert any(t.startswith("In dieser Instanz enthält keine neue Spalte einen Kreis") for _k, t in _verdicts(at))


def test_the_cycle_over_customer_7_does_not_pay_at_dual_price_5_but_pays_at_6():
    """Handrechnung am Handbeispiel: der Weg 7 → 6 → 7 → 6 hat bei Dualpreis d für Kunde 7 reduzierte Kosten 14 − (2d + 12); der beste elementare Weg hat −8 (bis d = 7): bei d = 5 gleichauf (−8), bei d = 6 besser (−10)."""
    for d7, lohnt in ((5, False), (6, True)):
        at = _fresh_app()
        _regler(at, "h_dual7").set_value(d7).run(timeout=TIMEOUT)
        text = next(t for _k, t in _verdicts(at) if t.startswith("Mit erlaubten Kreisen hat der beste Weg"))
        assert (f"bei Dualpreis {d7} für Kunde 7 lohnt sich dieser Kreis gegenüber" in text) == lohnt, text


def test_the_expanders_are_found_by_title_and_the_math_one_starts_with_the_reading_aid():
    at = _fresh_app()
    titel = [e.label for e in at.expander]
    assert "So funktioniert das Pricing mit Kreisen" in titel and "⚠️ Annahmen, Grenzen und bekannte Probleme" in titel
    mathe = _expander(at, "📐 Mathematische Formulierung")
    assert mathe.markdown[0].value.startswith("**Lesehilfe.**")
    assert "$$" in mathe.markdown[1].value


def test_app_text_of_assumptions_is_the_text_of_the_function():
    import kip_texte as T
    at = _fresh_app()
    assert _expander(at, "⚠️ Annahmen, Grenzen und bekannte Probleme").markdown[0].value == T.assumptions_markdown()


def test_live_cap_message_appears_when_the_cap_is_reached(monkeypatch):
    monkeypatch.setattr(C, "LIVE_MAX_VERGLEICHE_ELEMENTAR", 500)
    at = AppTest.from_file(APP_PATH, default_timeout=TIMEOUT)
    at.query_params["seed"] = "777"
    at.run(timeout=TIMEOUT)
    assert not at.exception
    assert any("an der Obergrenze der Live-Rechnung abgebrochen" in t for k, t in _verdicts(at) if k == "warning")
    assert any(m.label == "Schranke, elementar" and m.value == "nicht erreicht" for m in at.metric)


def test_round_control_shows_the_last_round_without_a_new_column():
    at = _fresh_app()
    _regler(at, "h_runde").set_value(C.HAND_RUNDE_MAX).run(timeout=TIMEOUT)
    assert any(i.value.startswith("In Runde 8 findet das Pricing keine Route mit negativen reduzierten Kosten") for i in at.info)
