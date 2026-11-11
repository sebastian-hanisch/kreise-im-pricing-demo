"""Presets (Schnellstart-Szenarien): Vollständigkeit, gültige Werte, Standard-Szenario = Standardeinstellungen, Permalink-Begrenzung."""

import pytest

import kip_constants as C
import kip_presets as P


def test_every_preset_has_help_and_sets_every_control():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.SETTING_SPECS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_valid_for_their_controls():
    for name, preset in C.PRESETS.items():
        for key, value in preset.items():
            spec = P.SETTING_SPECS[key]
            if spec.choices is not None:
                assert value in spec.choices, (name, key, value)
            else:
                assert spec.lo <= value <= spec.hi, (name, key, value)


def test_default_preset_equals_the_default_settings():
    first = next(iter(C.PRESETS.values()))
    assert {k: spec.default for k, spec in P.SETTING_SPECS.items()} == first


def test_presets_differ_from_each_other_in_at_least_one_control():
    werte = [tuple(sorted(p.items())) for p in C.PRESETS.values()]
    assert len(set(werte)) == len(werte)


def test_url_parameters_are_unique():
    params = [s.url_param for s in P.SETTING_SPECS.values()]
    assert len(params) == len(set(params))


@pytest.mark.parametrize("key, roh, erwartet", [
    ("l_n", "500", C.LIVE_N_MAX), ("l_n", "-3", C.LIVE_N_MIN), ("l_n", "abc", None), ("l_breite", "100", 100), ("l_breite", "70", None), ("l_breite", "200", 200),
    ("h_regel", C.HAND_REGELN[1], C.HAND_REGELN[1]), ("h_regel", "egal", None), ("h_dual7", "99", C.HAND_DUAL7_MAX), ("h_dual7", "0", C.HAND_DUAL7_MIN),
    ("h_runde", "9", C.HAND_RUNDE_MAX), ("h_runde", "4", 4), ("l_seed", "12345678", C.SEED_MAX), ("l_seed", "-5", 0),
])
def test_permalink_values_are_clamped_or_rejected(key, roh, erwartet):
    assert P._begrenzt(P.SETTING_SPECS[key], roh) == erwartet


def test_the_widths_of_the_live_control_include_the_widths_of_the_fixed_series():
    from kip_baender import kreise_breiten
    assert set(kreise_breiten()) <= set(C.LIVE_BREITEN)
