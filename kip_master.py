"""Master und Spaltenerzeugung: der Überdeckungs-Master (jeder Kunde mindestens einmal überdeckt) und die Schleife aus Master und Pricing.

Eine Spalte ist eine Route (Besuchsfolge); sie kostet ihre Weglänge. Besucht sie einen Kunden zweimal, zählt sie ihn im Master zweimal (Kreis-Spalten).
Zwei Master-Löser mit derselben Aufgabe:

* `master_lp`     HiGHS (scipy), Gleitkomma; für die Zufallsinstanzen,
* `master_exakt`  Simplex mit Brüchen (Regel von Bland), liefert Dualpreise und Mengen exakt; für das Handbeispiel (ganzzahlige Kosten).

`spaltenerzeugung` ruft abwechselnd einen Master-Löser und das Pricing (`kip_algorithm.price`) auf, bis keine Route mit negativen reduzierten Kosten mehr kommt;
der Wert des letzten Masters ist dann die untere Schranke (Schranke der Spaltenerzeugung) des Gedächtnisses k."""

from fractions import Fraction

import kip_algorithm as A
from kip_constants import EPS, MAX_NEUE_SPALTEN, NEG_RC


def _matrix(n: int, spalten: list):
    """Zeilen = Kunden 1..n, Spalten = Routen; Eintrag = Zahl der Besuche des Kunden in der Route."""
    import numpy as np
    a = np.zeros((n, len(spalten)))
    for c, route in enumerate(spalten):
        for j in route:
            a[j - 1, c] += 1
    return a


def master_lp(n: int, kosten: list, spalten: list):
    """Überdeckungs-Master  min c·x  mit  A x ≥ 1, x ≥ 0  mit HiGHS. Rückgabe (Zielwert, Dualpreise mit Position 0 = Depot = 0, Mengen x)."""
    import numpy as np
    from scipy.optimize import linprog
    a = _matrix(n, spalten)
    res = linprog(kosten, A_ub=-a, b_ub=-np.ones(n), bounds=(0, None), method="highs")
    if res.status != 0:
        raise RuntimeError(f"Master nicht lösbar: {res.message}")
    return float(res.fun), [0.0] + [float(v) for v in -res.ineqlin.marginals], [float(v) for v in res.x]


def master_exakt(n: int, kosten: list, spalten: list):
    """Derselbe Master, exakt mit Brüchen: Simplex auf dem Dualen  max Σπ  mit  Aᵀπ ≤ c, π ≥ 0 (Regel von Bland, also ohne Kreisen im Simplex).

    `kosten` ganzzahlig. Rückgabe (Zielwert, Dualpreise (Position 0 = Depot = 0), Mengen x) als Brüche."""
    m = len(spalten)
    tab = []
    for r, route in enumerate(spalten):
        zeile = [Fraction(0)] * (n + m)
        for j in route:
            zeile[j - 1] += 1
        zeile[n + r] = Fraction(1)
        tab.append(zeile + [Fraction(kosten[r])])
    ziel = [Fraction(1)] * n + [Fraction(0)] * m + [Fraction(0)]
    basis = [n + r for r in range(m)]
    while True:
        e = next((j for j in range(n + m) if ziel[j] > 0), None)
        if e is None:
            break
        beste = None
        for r in range(m):
            if tab[r][e] > 0:
                schluessel = (tab[r][-1] / tab[r][e], basis[r])
                if beste is None or schluessel < beste[0]:
                    beste = (schluessel, r)
        r = beste[1]
        piv = tab[r][e]
        tab[r] = [x / piv for x in tab[r]]
        for i in range(m):
            if i != r and tab[i][e] != 0:
                f = tab[i][e]
                tab[i] = [a - f * b for a, b in zip(tab[i], tab[r])]
        f = ziel[e]
        ziel = [a - f * b for a, b in zip(ziel, tab[r])]
        basis[r] = e
    dual = [Fraction(0)] * (n + 1)
    for r, b in enumerate(basis):
        if b < n:
            dual[b + 1] = tab[r][-1]
    return -ziel[-1], dual, [-ziel[n + r] for r in range(m)]


def spaltenerzeugung(inst, k: int, exakt: bool = False, max_neu: int = MAX_NEUE_SPALTEN, max_labels=None, max_vergleiche=None, max_runden: int = 400) -> dict:
    """Spaltenerzeugung mit Gedächtnis k: Start mit den Einzelfahrten Depot-i-Depot, je Runde Master und Pricing.

    Je Runde werden bis zu `max_neu` neue Routen (die besten nach reduzierten Kosten, noch nicht im Master, mit reduzierten Kosten unter der Schwelle) als Spalten aufgenommen.
    `exakt`: Master mit Brüchen und Pricing ohne Toleranz (ganzzahlige Instanzen); sonst HiGHS und Gleitkomma. `max_labels`, `max_vergleiche`: Obergrenzen für die erzeugten Labels
    und die Dominanztests in ALLEN Pricing-Aufrufen zusammen (None = unbegrenzt); bei Erreichen bricht die Rechnung ab (`abgebrochen`, keine Schranke).
    Rückgabe: schranke (Wert des letzten Masters oder None), runden (Liste von Wörterbüchern: nr, wert, dual, neue [(reduzierte Kosten, Route)], erzeugt),
    spalten (alle Routen, die ersten n sind die Einzelfahrten), kosten, mengen (Mengen des letzten Masters), labels (erzeugte Labels gesamt), vergleiche (Dominanztests gesamt), abgebrochen."""
    n = inst.n
    master = master_exakt if exakt else master_lp
    eps, neg = (0, 0) if exakt else (EPS, NEG_RC)
    spalten = [(j,) for j in range(1, n + 1)]
    kosten = [A.weg_laenge(inst, r) for r in spalten]
    bekannt = set(spalten)
    runden, labels, vergleiche, wert, mengen = [], 0, 0, None, []
    abgebrochen = False
    for nr in range(1, max_runden + 1):
        wert, dual, mengen = master(n, kosten, spalten)
        rest = None if max_labels is None else max_labels - labels
        rest_v = None if max_vergleiche is None else max_vergleiche - vergleiche
        res = A.price(inst, dual, k, max_routes=max_neu, max_labels=rest, max_vergleiche=rest_v, eps=eps, neg=neg)
        labels += res.erzeugt
        vergleiche += res.vergleiche
        if res.abgebrochen:
            abgebrochen = True
            runden.append({"nr": nr, "wert": wert, "dual": dual, "neue": [], "erzeugt": res.erzeugt})
            break
        neue = []
        for _rc, route in res.routen:
            if route in bekannt:
                continue
            rc = A.route_kosten(inst, dual, route)
            if rc < neg:
                neue.append((rc, route))
        runden.append({"nr": nr, "wert": wert, "dual": dual, "neue": neue, "erzeugt": res.erzeugt})
        if not neue:
            break
        for _rc, route in neue:
            spalten.append(route)
            kosten.append(A.weg_laenge(inst, route))
            bekannt.add(route)
    return {"schranke": None if abgebrochen else wert, "runden": runden, "spalten": spalten, "kosten": kosten, "mengen": mengen,
            "labels": labels, "vergleiche": vergleiche, "abgebrochen": abgebrochen}


def neue_spalten(lauf: dict, n: int) -> list:
    """Die in der Spaltenerzeugung neu aufgenommenen Routen (ohne die n Einzelfahrten) in der Reihenfolge der Aufnahme."""
    return lauf["spalten"][n:]


def endloesung(lauf: dict, rauschgrenze: float = 1e-9) -> list:
    """Spalten mit positiver Menge im letzten Master als [(Route, Menge)]; Mengen unter der Rauschgrenze zählen als null."""
    return [(r, x) for r, x in zip(lauf["spalten"], lauf["mengen"]) if x > rauschgrenze]
