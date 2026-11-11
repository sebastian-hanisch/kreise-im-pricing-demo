"""Kennzahlen, Verdikt-Logik und Auswertung der Läufe (Handbeispiel, Live-Rechnung, feste Messreihen).

Jedes Verdikt der App ist eine reine Funktion `verdict_*(...) -> (Art, Text)`; die App ruft `getattr(st, Art)(Text)`, `tests/test_verdicts.py` prüft Schwellen und jede Zahl im Text.
Zahlen im Text kommen aus der Rechnung (f-String), nie aus dem Kopf."""

import time
from fractions import Fraction

import kip_algorithm as A
import kip_constants as C
import kip_master as M
import kip_scenario as S

# ---------------------------------------------------------------------------------------------------------------------------------
# Zahlenformat (Dezimalkomma, geschütztes Leerzeichen als Tausendertrenner)
# ---------------------------------------------------------------------------------------------------------------------------------

NBSP = " "


def fmt_int(x) -> str:
    return f"{round(x):,}".replace(",", NBSP).replace("-", "−")


def fmt_dec(x, stellen: int = 1) -> str:
    return f"{float(x):,.{stellen}f}".replace(",", NBSP).replace(".", ",").replace("-", "−")


def fmt_pct(anteil, stellen: int = 1) -> str:
    """Anteil (0 bis 1) als Prozentangabe mit Dezimalkomma."""
    return fmt_dec(100 * anteil, stellen) + NBSP + "%"


def fmt_wert(x, stellen: int = 2) -> str:
    """Ganze Zahl ohne Nachkommastellen, echter Bruch als „83/3 (27,67)“, Gleitkommazahl mit Dezimalkomma."""
    if isinstance(x, Fraction) and x.denominator != 1:
        return f"{x.numerator}/{x.denominator}".replace("-", "−") + f" ({fmt_dec(float(x), stellen)})"
    if isinstance(x, (int, Fraction)):
        return fmt_int(x)
    return fmt_dec(x, stellen)


def weg_text(route) -> str:
    return " → ".join(str(j) for j in route) if route else "kein Weg mit negativen Kosten"


def doppelt_text(route) -> str:
    """„Kunde 7 und 6 doppelt“ für die mehrfach besuchten Kunden einer Route, sonst ein leerer Text."""
    d = A.doppelte_kunden(route)
    if not d:
        return ""
    namen = [str(j) for j in d]
    return ("Kunde " + " und ".join(namen) + " mehrfach") if len(namen) == 1 else ("Kunden " + " und ".join(namen) + " mehrfach")


def nachbarn_mengen(inst, k: int) -> list:
    """Nachbarschaft NG(j) als Menge, unabhängig von der Bitmaske des Kerns gebildet (der Kunde selbst und die k − 1 nächsten, Gleichstand: kleinere Nummer)."""
    mengen = [set()]
    for j in range(1, inst.n + 1):
        andere = sorted((i for i in range(1, inst.n + 1) if i != j), key=lambda i: (inst.dist[j][i], i))
        mengen.append({j, *andere[: max(k - 1, 0)]})
    return mengen


def laenge_text(k) -> str:
    """Kürzester Kreis in Worten: 2 Kanten = i, j, i."""
    return {"2": "zwei Kanten (i, j, i)", "3": "drei Kanten (i, j, l, i)", "4+": "vier oder mehr Kanten"}[k]


# ---------------------------------------------------------------------------------------------------------------------------------
# Handbeispiel, Experiment 1: der Kreis im Labeling
# ---------------------------------------------------------------------------------------------------------------------------------

HAND_N = 7


def hand_k(regel: str) -> int:
    """Gedächtnis k der gewählten Regel: 1 (Kreise erlaubt) oder 7 (elementar)."""
    return 1 if regel == C.HAND_REGELN[0] else HAND_N


def hand_lauf(k: int, dual7: int, mit_protokoll: bool = False):
    """Ein Pricing-Aufruf am Handbeispiel, exakt gerechnet (ganze Zahlen). Rückgabe (Ergebnis, Protokoll oder None)."""
    protokoll = [] if mit_protokoll else None
    res = A.price(S.handbeispiel(), S.hand_dualpreise(dual7), k, eps=0, neg=0, trace=protokoll)
    return res, protokoll


def _zeile_regel(inst, dual, k: int) -> dict:
    """Kennzahlen einer Regel (k = 1 oder elementar) am Handbeispiel samt Gegenprobe durch Aufzählung und Prüfung des besten Weges."""
    elementar = k >= inst.n
    res = A.price(inst, dual, k, eps=0, neg=0)
    wert, weg, wege, mit_kreis, negativ = A.aufzaehlung(inst, dual, elementar, 0)
    fehler = None
    if res.routen:
        fehler = A.pruefe_route(inst, res.routen[0][1], nachbarn_mengen(inst, k), 0)
        if fehler is None and A.route_kosten(inst, dual, res.routen[0][1]) != res.bester_wert:
            fehler = "reduzierte Kosten der Route stimmen nicht mit dem Label überein"
    if fehler is None and wert != res.bester_wert:
        fehler = f"Aufzählung findet {wert}, das Label-Setting {res.bester_wert}"
    return {"erzeugt": res.erzeugt, "dominiert": res.dominiert, "anteil": res.anteil_dominiert, "bester_wert": res.bester_wert,
            "weg": res.routen[0][1] if res.routen else (), "aufz_wert": wert, "aufz_wege": wege, "aufz_kreis": mit_kreis, "aufz_negativ": negativ, "fehler": fehler}


def hand_kreis(dual7: int) -> dict:
    """Experiment 1: dieselbe Runde mit erlaubten Kreisen (k = 1) und elementar, dazu der beste Weg, der Kunde 7 mindestens zweimal besucht.

    Rückgabe {"k1": Zeile, "elem": Zeile, "kunde7": (reduzierte Kosten, Weg) oder None}; `kunde7` sucht unter allen zulässigen Wegen ohne direkte Wiederholung."""
    inst, dual = S.handbeispiel(), S.hand_dualpreise(dual7)
    zweimal = [(A.route_kosten(inst, dual, r), r) for r in A.alle_routen(inst, False, 0) if r.count(S.HAND_KUNDE_MIT_PREIS) >= 2]
    return {"k1": _zeile_regel(inst, dual, 1), "elem": _zeile_regel(inst, dual, inst.n), "kunde7": min(zweimal) if zweimal else None}


def aufstellung(inst, dual, route) -> dict:
    """Rechnung eines Weges in Worten: Entfernungen (Depot, Route, Depot), Dualpreise je Besuch, reduzierte Kosten."""
    folge = (0,) + tuple(route) + (0,)
    dist = [inst.dist[a][b] for a, b in zip(folge, folge[1:])]
    preise = [dual[j] for j in route]
    return {"entfernungen": dist, "summe_entfernung": sum(dist), "dualpreise": preise, "summe_dual": sum(preise), "wert": sum(dist) - sum(preise)}


def aufstellung_text(inst, dual, route) -> str:
    """Zum Beispiel „Entfernungen 5 + 2 + 2 + 2 + 3 = 14; Dualpreise 10 + 6 + 10 + 6 = 32; reduzierte Kosten 14 − 32 = −18“ (jeder Besuch zählt)."""
    a = aufstellung(inst, dual, route)
    return (f"Entfernungen {' + '.join(fmt_wert(x) for x in a['entfernungen'])} = {fmt_wert(a['summe_entfernung'])}; "
            f"Dualpreise {' + '.join(fmt_wert(x) for x in a['dualpreise'])} = {fmt_wert(a['summe_dual'])}; "
            f"reduzierte Kosten {fmt_wert(a['summe_entfernung'])} − {fmt_wert(a['summe_dual'])} = {fmt_wert(a['wert'])}")


def label_tabelle(protokoll: list) -> list:
    """Alle erzeugten Labels des Protokolls in Reihenfolge der Erzeugung (Nummern wie im Protokoll des Kerns).

    Je Zeile: id, weg, kunde, zeit, kosten, last, von (Nummer des dominierenden Labels oder None), abgeloest_von (Nummer des Labels, das dieses später abgelöst hat, oder None)."""
    parent_of, kunde_of, zeilen, index = {}, {}, [], {}
    for e in protokoll:
        if e[0] == "neu":
            _, lid, parent, kunde, zeit, kosten, last, von = e
            parent_of[lid], kunde_of[lid] = parent, kunde
            weg, x = [], lid
            while x != -1:
                weg.append(kunde_of[x])
                x = parent_of[x]
            zeile = {"id": lid, "weg": tuple(reversed(weg))[1:], "kunde": kunde, "zeit": zeit, "kosten": kosten, "last": last, "von": von, "abgeloest_von": None}
            index[lid] = zeile
            zeilen.append(zeile)
        else:
            _, alt, neu = e
            index[alt]["abgeloest_von"] = neu
    return zeilen


def entscheidung_text(zeile: dict) -> str:
    if zeile["von"] is not None:
        return f"fällt weg: dominiert von L{zeile['von']}"
    if zeile["abgeloest_von"] is not None:
        return f"bleibt zunächst, entfällt später: dominiert von L{zeile['abgeloest_von']}"
    return "bleibt"


def ueberlebende_tabelle(tabelle: list) -> list:
    """Die Labels, die am Ende noch leben (nicht verworfen, nicht abgelöst), nach Kunde und Zeit geordnet (ohne das Startlabel am Depot)."""
    lebend = [z for z in tabelle if z["von"] is None and z["abgeloest_von"] is None and z["id"] != 0]
    return sorted(lebend, key=lambda z: (z["kunde"], z["zeit"], z["id"]))


# ---------------------------------------------------------------------------------------------------------------------------------
# Handbeispiel, Experiment 2: Spaltenerzeugung Runde für Runde
# ---------------------------------------------------------------------------------------------------------------------------------

def hand_spaltenerzeugung(elementar: bool) -> dict:
    """Spaltenerzeugung am Handbeispiel, exakt mit Brüchen, je Runde die beste neue Spalte (Gleichstand: kleinere Besuchsfolge).

    Rückgabe: lauf (Ergebnis von `spaltenerzeugung`), neue (die neu aufgenommenen Routen), mit_kreis (wie viele davon), ende (Spalten mit positiver Menge), schranke, labels, runden (Zahl)."""
    inst = S.handbeispiel()
    lauf = M.spaltenerzeugung(inst, inst.n if elementar else 1, exakt=True, max_neu=1)
    neue = M.neue_spalten(lauf, inst.n)
    return {"lauf": lauf, "neue": neue, "mit_kreis": sum(1 for r in neue if A.hat_kreis(r)), "ende": M.endloesung(lauf, 0),
            "schranke": lauf["schranke"], "labels": lauf["labels"], "runden": len(lauf["runden"])}


def hand_gegenprobe(elementar: bool) -> dict:
    """Gegenprobe zur Spaltenerzeugung: alle zulässigen Routen als Spalten, ein Master (exakt) darüber. Rückgabe {"wert": ..., "spalten": Zahl}."""
    inst = S.handbeispiel()
    routen = A.alle_routen(inst, elementar, 0)
    wert, _dual, _x = M.master_exakt(inst.n, [A.weg_laenge(inst, r) for r in routen], routen)
    return {"wert": wert, "spalten": len(routen)}


def luecke(schranke_ref, schranke):
    """Lücke = (Schranke der Bezugsrechnung − Schranke) / Schranke der Bezugsrechnung (als Anteil, 0 bis 1); None, wenn eine der beiden fehlt."""
    if schranke is None or schranke_ref is None or schranke_ref == 0:
        return None
    return (schranke_ref - schranke) / schranke_ref


# ---------------------------------------------------------------------------------------------------------------------------------
# Live-Rechnung, Experiment 3 und 4
# ---------------------------------------------------------------------------------------------------------------------------------

def kreis_kennzahlen(spalten: list) -> dict:
    """Kennzahlen der Kreise in einer Liste von Routen: Zahl der Routen, Zahl mit Kreis, kürzester Kreis in Kanten (2, 3, 4 und mehr), Zahl der Wiederholungen je Route."""
    kuerzeste, wdh = {"2": 0, "3": 0, "4+": 0}, {}
    mit = [r for r in spalten if A.hat_kreis(r)]
    for r in mit:
        k = A.kuerzester_kreis(r)
        kuerzeste["2" if k == 2 else "3" if k == 3 else "4+"] += 1
        wdh[A.wiederholungen(r)] = wdh.get(A.wiederholungen(r), 0) + 1
    return {"spalten": len(spalten), "mit_kreis": len(mit), "kuerzeste": kuerzeste, "wiederholungen": dict(sorted(wdh.items()))}


def live_lauf(n: int, breite: int, seed: int) -> dict:
    """Ganze Spaltenerzeugung auf einer zufälligen Instanz: einmal mit erlaubten Kreisen (k = 1), einmal elementar (mit Obergrenze in Dominanztests).

    Jede neue Spalte der Rechnung mit Kreisen wird vor der Anzeige unabhängig geprüft (`pruefe_route`); die Schranke bei k = 1 darf nie über der elementaren liegen.
    Rückgabe: Kennzahlen beider Läufe, Kreis-Kennzahlen der neuen Spalten, Lücke (None, wenn die elementare Rechnung abbrach), `fehler` (None, wenn alle Prüfungen bestanden) und die Rechenzeit (nur zur Information)."""
    inst = S.make_instance(n, seed, breite)
    t0 = time.perf_counter()
    k1 = M.spaltenerzeugung(inst, 1)
    el = M.spaltenerzeugung(inst, n, max_vergleiche=C.LIVE_MAX_VERGLEICHE_ELEMENTAR)
    sekunden = time.perf_counter() - t0
    neue = M.neue_spalten(k1, n)
    ende = M.endloesung(k1, C.MENGE_EPS)
    fehler = None
    nb = nachbarn_mengen(inst, 1)
    for r in neue:
        f = A.pruefe_route(inst, r, nb)
        if f is not None:
            fehler = f"Spalte {weg_text(r)}: {f}"
            break
    if fehler is None and el["schranke"] is not None and k1["schranke"] > el["schranke"] + 1e-6:
        fehler = "die Schranke bei k = 1 liegt über der elementaren"
    return {
        "n": n, "breite": breite, "seed": seed, "sekunden": sekunden, "fehler": fehler,
        "k1": {"schranke": k1["schranke"], "runden": len(k1["runden"]), "labels": k1["labels"], "vergleiche": k1["vergleiche"], **kreis_kennzahlen(neue),
               "ende_spalten": len(ende), "ende_kreis": sum(1 for r, _x in ende if A.hat_kreis(r))},
        "elem": {"schranke": el["schranke"], "runden": len(el["runden"]), "labels": el["labels"], "vergleiche": el["vergleiche"], "abgebrochen": el["abgebrochen"]},
        "luecke": luecke(el["schranke"], k1["schranke"]),
    }


# ---------------------------------------------------------------------------------------------------------------------------------
# Verdikte (reine Funktionen)
# ---------------------------------------------------------------------------------------------------------------------------------

def _gross(text: str) -> str:
    return text[:1].upper() + text[1:]


def verdict_kreis_hand(z1: dict, ze: dict, kunde7, dual7) -> tuple:
    """Verdikt zu Experiment 1: bester Weg mit Kreisen gegen bester elementarer Weg, und ob sich der Kreis über Kunde 7 lohnt.

    `z1`, `ze`: Zeilen von `hand_kreis` (k1, elem); `kunde7`: (reduzierte Kosten, Weg) des besten Weges mit Kunde 7 mindestens zweimal oder None; `dual7`: Dualpreis von Kunde 7.
    Der Kreis über Kunde 7 lohnt sich, wenn dieser Weg strikt bessere (kleinere) reduzierte Kosten hat als der beste elementare Weg."""
    if not z1["weg"] and not ze["weg"]:
        return "info", "Bei diesen Dualpreisen hat kein Weg negative reduzierte Kosten, weder mit erlaubten Kreisen noch elementar: es gibt keine neue Spalte."
    b1, be = z1["bester_wert"], ze["bester_wert"]
    teil1 = (f"Mit erlaubten Kreisen hat der beste Weg reduzierte Kosten {fmt_wert(b1)} (Weg {weg_text(z1['weg'])}"
             f"{', ' + doppelt_text(z1['weg']) if A.hat_kreis(z1['weg']) else ', ohne Kreis'}), elementar {fmt_wert(be)} (Weg {weg_text(ze['weg'])}); ")
    if b1 < be:
        teil1 += f"der Kreis macht den besten Weg um {fmt_wert(be - b1)} günstiger."
    else:
        teil1 += "mit erlaubten Kreisen gibt es hier keinen besseren Weg."
    if kunde7 is None:
        teil2 = f" Ein Weg, der Kunde {S.HAND_KUNDE_MIT_PREIS} zweimal besucht, ist bei diesen Fenstern und dieser Last nicht zulässig."
        return "info", teil1 + teil2
    rc7, weg7 = kunde7
    lohnt = rc7 < be
    teil2 = (f" Der beste Weg mit Kunde {S.HAND_KUNDE_MIT_PREIS} mindestens zweimal (Weg {weg_text(weg7)}) hat reduzierte Kosten {fmt_wert(rc7)}: "
             f"bei Dualpreis {fmt_wert(dual7)} für Kunde {S.HAND_KUNDE_MIT_PREIS} lohnt sich dieser Kreis {'gegenüber dem besten elementaren Weg' if lohnt else 'nicht gegenüber dem besten elementaren Weg'} ({fmt_wert(be)}).")
    return ("success" if lohnt else "info"), teil1 + teil2


def verdict_colgen_hand(k1: dict, el: dict, gegenprobe_k1: dict, gegenprobe_el: dict) -> tuple:
    """Verdikt zu Experiment 2: Schranke der Spaltenerzeugung mit Kreisen gegen die elementare, Lücke, Zahl der Spalten mit Kreis.

    `k1`, `el`: Ergebnisse von `hand_spaltenerzeugung`; `gegenprobe_*`: Ergebnisse von `hand_gegenprobe` (Master über alle zulässigen Routen)."""
    lk = luecke(el["schranke"], k1["schranke"])
    gleich = gegenprobe_k1["wert"] == k1["schranke"] and gegenprobe_el["wert"] == el["schranke"]
    text = (f"Spaltenerzeugung im Handbeispiel: mit erlaubten Kreisen endet sie nach {k1['runden']} Runden bei der Schranke {fmt_wert(k1['schranke'])}, elementar nach {el['runden']} Runden bei {fmt_wert(el['schranke'])}. "
            f"{k1['mit_kreis']} von {len(k1['neue'])} neuen Spalten enthalten einen Kreis. Labels insgesamt: {fmt_int(k1['labels'])} mit erlaubten Kreisen, {fmt_int(el['labels'])} elementar. "
            f"Gegenprobe (ein Master über alle {gegenprobe_k1['spalten']} bzw. {gegenprobe_el['spalten']} zulässigen Routen): {'gleiche Schranken' if gleich else 'ABWEICHUNG'}.")
    if lk is None or lk == 0:
        return "info", text + " Die beiden Schranken sind gleich."
    return "warning", text + f" Die Schranke mit erlaubten Kreisen liegt {fmt_pct(lk, 2)} unter der elementaren (Lücke = Unterschied geteilt durch die elementare Schranke)."


def verdict_live(z: dict) -> tuple:
    """Verdikt zu Experiment 3 (eine Instanz): Anteil der Spalten mit Kreis, Schranken und Lücke; bricht die elementare Rechnung ab, gibt es keine Lücke."""
    k1, el = z["k1"], z["elem"]
    anteil = f"{k1['mit_kreis']} von {k1['spalten']} neuen Spalten" + (f" ({fmt_pct(k1['mit_kreis'] / k1['spalten'])})" if k1["spalten"] else "") + " enthalten einen Kreis"
    kopf = f"{_gross(anteil)} (n = {z['n']}, Breite {z['breite']}, Zufalls-Seed {z['seed']}); Schranke mit erlaubten Kreisen {fmt_dec(k1['schranke'], 2)}"
    if el["abgebrochen"]:
        return "warning", (f"{kopf}. Die elementare Rechnung wurde an der Obergrenze der Live-Rechnung abgebrochen ({fmt_int(el['vergleiche'])} Dominanztests, {fmt_int(el['labels'])} Labels): "
                           "für diese Einstellung gibt es keine elementare Schranke und keine Lücke.")
    text = f"{kopf}, elementar {fmt_dec(el['schranke'], 2)}"
    if z["luecke"] is None or z["luecke"] <= 1e-9:
        return "info", text + ": die Schranken sind gleich (Lücke 0), obwohl Kreise erlaubt waren."
    return "warning", text + f": die Schranke mit erlaubten Kreisen liegt {fmt_pct(z['luecke'], 2)} unter der elementaren."


def verdict_kreislaengen(live: dict, fest: dict, breite: int) -> tuple:
    """Verdikt zu Experiment 4: welcher kürzeste Kreis kommt vor? `live`: kreis_kennzahlen der gewählten Instanz; `fest`: Summen der festen Messreihe der gleichen Breite (n = 30)."""
    f = fest["kuerzeste"]
    fest_text = (f"In der festen Messreihe (n = 30, Breite {breite}, {fest['instanzen']} Instanzen) haben von {fmt_int(fest['mit_kreis'])} Kreis-Spalten {fmt_int(f['2'])} "
                 f"({fmt_pct(f['2'] / fest['mit_kreis'])}) als kürzesten Kreis zwei Kanten (i, j, i)" if fest["mit_kreis"] else f"In der festen Messreihe (Breite {breite}) gibt es keine Kreis-Spalten")
    if live["mit_kreis"] == 0:
        return "info", f"In dieser Instanz enthält keine neue Spalte einen Kreis. {fest_text}."
    kz = live["kuerzeste"]
    return "success", (f"In dieser Instanz haben von {live['mit_kreis']} Kreis-Spalten {kz['2']} als kürzesten Kreis zwei Kanten (i, j, i), {kz['3']} drei Kanten und {kz['4+']} vier oder mehr. {fest_text}.")


def verdict_kreise_baender(tabelle: list) -> tuple:
    """Verdikt zu Experiment 5a: Anteil der neuen Spalten mit Kreis und in der Endlösung je Breite. `tabelle`: Zeilen von `kip_baender.kreise_tabelle`."""
    teile = [f"Breite {z['breite']}: {fmt_pct(z['anteil_neue'])} der neuen Spalten ({fmt_int(z['mit_kreis'])} von {fmt_int(z['neue_spalten'])}), {fmt_pct(z['anteil_ende'])} der Spalten der Endlösung ({z['ende_kreis']} von {z['ende_spalten']})"
             for z in tabelle]
    wachsend = all(b["anteil_neue"] > a["anteil_neue"] for a, b in zip(tabelle, tabelle[1:]))
    text = f"Anteil der Spalten mit Kreis (n = 30, k = 1, {tabelle[0]['instanzen']} Instanzen je Breite): " + "; ".join(teile) + "."
    return ("success" if wachsend else "info"), text + (" Der Anteil wächst mit der Breite." if wachsend else " Der Anteil wächst nicht mit jeder Breite.")


def verdict_luecke_baender(zeilen: list) -> tuple:
    """Verdikt zu Experiment 5b: Lücke zur elementaren Schranke. `zeilen`: Kennzahlen der Zellen (n, breite, instanzen_fertig, mittel, max) mit Bezug „elementar“, ohne n = 30."""
    je_breite = {}
    for z in zeilen:
        je_breite.setdefault(z["breite"], []).append(z)
    teile = []
    for b, zs in sorted(je_breite.items()):
        teile.append(f"Breite {b}: " + ", ".join(f"n = {z['n']}: {fmt_dec(100 * z['mittel'], 2)}{NBSP}%" for z in sorted(zs, key=lambda z: z["n"])))
    return "info", ("Mittlere Lücke der Schranke mit erlaubten Kreisen zur elementaren (Mittel über Instanzen mit fertiger elementarer Rechnung; "
                    + "; ".join(teile) + "). Aussagen gelten nur für diese Breiten und Größen.")


def hand_halbe_kreisfahrt(cg: dict, inst):
    """Die „halbe Kreisfahrt“ der Endlösung im Handbeispiel: eine Spalte mit Menge 1/2, in der jeder Kunde genau zweimal vorkommt.

    Sie überdeckt jeden ihrer Kunden einmal und kostet halb so viel wie die ganze Route; die elementare Fahrt durch dieselben Kunden (in der Reihenfolge des ersten Besuchs) wird daneben gestellt.
    Rückgabe ein Wörterbuch (route, menge, doppelt, kosten, anteilig, elementar_route, elementar_kosten) oder None, wenn es eine solche Spalte nicht gibt."""
    for route, x in cg["ende"]:
        if x == Fraction(1, 2) and all(route.count(j) == 2 for j in set(route)):
            elementar = tuple(dict.fromkeys(route))
            kosten = A.weg_laenge(inst, route)
            return {"route": route, "menge": x, "doppelt": sorted(set(route)), "kosten": kosten, "anteilig": x * kosten, "elementar_route": elementar, "elementar_kosten": A.weg_laenge(inst, elementar)}
    return None
