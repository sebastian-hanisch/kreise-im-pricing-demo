"""Feste Messreihen (data/*.json): Zellen auswählen und Kennzahlen bilden (Mittel, Maximum, Median, Zahl fertiger und abgebrochener Läufe).

Nichts hier rechnet das Label-Setting neu. Die Rohwerte je Instanz stehen in den JSON-Dateien; `tools/baender_erzeugen.py` hat sie mit dem Kern dieser Demo gerechnet
(Ausnahme: die Zellen „k = 16“ stammen nur aus der Auswertungsdatei der Vormessung und sind nicht neu gerechnet; jede Zelle nennt ihre Quelle). Gerechnet wird hier nur über die Instanzen einer Zelle.
Zeilen abgebrochener Läufe zählen nicht in die Mittel (sie fehlen bei zähen Zellen)."""

import json
from functools import lru_cache
from pathlib import Path
from statistics import mean, median

import kip_constants as C

DATA = Path(__file__).resolve().parent / "data"
NULL_LUECKE = 1e-6       # eine Lücke unter diesem Anteil (relativ zur Bezugsschranke) zählt als null
TYPEN = {"zufall": "zufällig", "cluster": "gruppiert", "lang": "lang (Horizont 500, Kapazität 120)"}


@lru_cache(maxsize=None)
def _lade(name: str) -> dict:
    return json.loads((DATA / name).read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------------------------------------------------------------
# Anteil der Spalten mit Kreis (Experiment 5a)
# ---------------------------------------------------------------------------------------------------------------------------------

def kreise_zelle(breite: int) -> dict:
    return next(z for z in _lade(C.BAND_FILE_KREISE)["zellen"] if z["breite"] == breite)


def kreise_breiten() -> list:
    return [z["breite"] for z in _lade(C.BAND_FILE_KREISE)["zellen"]]


def kreise_summe(breite: int) -> dict:
    """Summen über die Instanzen einer Breite: neue Spalten, davon mit Kreis, Spalten der Endlösung (Menge über der Rauschgrenze), davon mit Kreis, Anteil an der Menge,
    kürzester Kreis (2, 3, 4 und mehr Kanten), Zahl der Wiederholungen je Kreis-Spalte, mittlere Länge (Kunden je Spalte) aller neuen und der Kreis-Spalten."""
    zeilen = kreise_zelle(breite)["zeilen"]
    neue, kreis = sum(z["neue_spalten"] for z in zeilen), sum(z["mit_kreis"] for z in zeilen)
    ende, ende_kreis = sum(z["ende_spalten"] for z in zeilen), sum(z["ende_kreis"] for z in zeilen)
    menge, menge_kreis = sum(z["ende_menge"] for z in zeilen), sum(z["ende_menge_kreis"] for z in zeilen)
    kuerzeste = {k: sum(z["kuerzester_kreis"][k] for z in zeilen) for k in ("2", "3", "4+")}
    wdh = {}
    for z in zeilen:
        for k, v in z["wiederholungen"].items():
            wdh[int(k)] = wdh.get(int(k), 0) + v
    return {
        "breite": breite, "instanzen": len(zeilen), "neue_spalten": neue, "mit_kreis": kreis, "anteil_neue": kreis / neue,
        "ende_spalten": ende, "ende_kreis": ende_kreis, "anteil_ende": ende_kreis / ende, "anteil_menge": menge_kreis / menge,
        "kuerzeste": kuerzeste, "wiederholungen": dict(sorted(wdh.items())),
        "laenge_neue": sum(z["laenge_neue"] for z in zeilen) / neue, "laenge_kreis": sum(z["laenge_kreis"] for z in zeilen) / kreis if kreis else None,
    }


def kreise_tabelle() -> list:
    return [kreise_summe(b) for b in kreise_breiten()]


# ---------------------------------------------------------------------------------------------------------------------------------
# Lücke der Schranke (Experiment 5b)
# ---------------------------------------------------------------------------------------------------------------------------------

def luecke_zellen() -> list:
    return _lade(C.BAND_FILE_LUECKE)["zellen"]


def luecke_zelle(zid: str) -> dict:
    return next(z for z in luecke_zellen() if z["id"] == zid)


def luecke_zeile(z: dict):
    """Lücke einer Instanz als Anteil (Bezugsschranke − Schranke bei k = 1) / Bezugsschranke; None, wenn der Bezugslauf abbrach."""
    if z["abgebrochen"] or z["schranke_ref"] is None:
        return None
    return (z["schranke_ref"] - z["schranke_k1"]) / z["schranke_ref"]


def luecke_kennzahlen(zelle: dict) -> dict:
    """Kennzahlen einer Zelle mit Einzelwerten: Zahl der Instanzen, fertige und abgebrochene Läufe, Lücke (Mittel und Maximum, Anteile), Zahl der Instanzen mit Lücke null,
    Median der erzeugten Labels bei k = 1 und im Bezug (nur fertige Läufe). Zellen ohne Einzelwerte (nicht neu gerechnet) haben ihre Zusammenfassung unter `zusammenfassung`."""
    zeilen = zelle["zeilen"]
    fertig = [z for z in zeilen if luecke_zeile(z) is not None]
    gaps = [luecke_zeile(z) for z in fertig]
    return {
        "n": zelle["n"], "breite": zelle["breite"], "typ": zelle["typ"], "bezug": zelle["bezug"], "instanzen": len(zeilen), "fertig": len(fertig), "abgebrochen": len(zeilen) - len(fertig),
        "mittel": mean(gaps) if gaps else None, "maximum": max(gaps) if gaps else None, "null_in": sum(1 for g in gaps if g <= NULL_LUECKE),
        "labels_k1": median(z["labels_k1"] for z in fertig) if fertig else None, "labels_ref": median(z["labels_ref"] for z in fertig) if fertig else None,
    }


def luecke_elementar_tabelle() -> list:
    """Zeilen für Bezug „elementar“: n = 10 bis 30, Breite 40 und 100."""
    zs = [z for z in luecke_zellen() if z["bezug"] == "elementar"]
    return [luecke_kennzahlen(z) for z in sorted(zs, key=lambda z: (z["breite"], z["n"]))]


def luecke_k8_tabelle() -> list:
    return [luecke_kennzahlen(z) for z in luecke_zellen() if z["bezug"] == "k = 8"]


def luecke_k16_tabelle() -> list:
    """Zeilen für Bezug „k = 16“ (nur aus der Auswertungsdatei übernommen, nicht neu gerechnet)."""
    out = []
    for z in luecke_zellen():
        if z["bezug"] == "k = 16":
            s = z["zusammenfassung"]
            out.append({"n": s["n"], "breite": s["breite"], "typ": s["typ"], "instanzen": s["instanzen"], "mittel": s["luecke_mittel"] / 100, "maximum": s["luecke_max"] / 100,
                        "null_in": s["luecke_null_in"], "labels_k1": s["labels_median_k1"], "labels_ref": s["labels_median_k16"]})
    return sorted(out, key=lambda z: (z["typ"], z["n"], z["breite"]))


def vormessung_vergleiche() -> dict:
    """Wie viele neu gerechnete Schranken wurden mit der Vormessung verglichen, und wie viele wichen ab (Toleranz 1e-3)? Rückgabe {"verglichen": a, "abweichend": b}."""
    verglichen = abweichend = 0
    for z in luecke_zellen():
        v = z.get("vormessung")
        if not v:
            continue
        for k in ("k1", "elementar", "k1_und_k8"):
            if k in v:
                verglichen += v[k]["verglichen"]
                abweichend += v[k]["abweichend"]
    return {"verglichen": verglichen, "abweichend": abweichend}


BEZUEGE = {"elementar": "elementar (neu gerechnet)", "k = 8": "k = 8 (neu gerechnet)", "k = 16": "k = 16 (nicht neu gerechnet)"}


def grenze_vergleiche() -> int:
    """Obergrenze in Dominanztests der elementaren Läufe der Messreihe (Zählung, keine Zeitgrenze)."""
    return luecke_zelle("elementar_n30_b100")["grenze_vergleiche"]


def luecke_n30_vergleich():
    """n = 30, Breite 100, Bezug elementar: wie viele Läufe waren in der Messung vor dem Bau fertig, und wie ändert sich die mittlere Lücke, wenn alle Läufe fertig sind?

    Rückgabe (instanzen, fertig_vor, abgebrochen_vor, mittel_vor, fertig_hier, mittel_hier) mit Mitteln als Anteil, oder None, wenn die Zelle keinen Vergleich mit der Messung vor dem Bau enthält."""
    z = luecke_zelle("elementar_n30_b100")
    v = z.get("vormessung")
    if not v:
        return None
    nur_hier = set(v["elementar"]["nur_neu_fertig_seeds"])
    vor = [luecke_zeile(r) for r in z["zeilen"] if r["seed"] not in nur_hier and luecke_zeile(r) is not None]
    hier = [luecke_zeile(r) for r in z["zeilen"] if luecke_zeile(r) is not None]
    return {"instanzen": len(z["zeilen"]), "fertig_vor": len(vor), "abgebrochen_vor": len(z["zeilen"]) - len(vor), "mittel_vor": mean(vor), "fertig_hier": len(hier), "mittel_hier": mean(hier)}
