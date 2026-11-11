"""Kern der Demo (nur Standardbibliothek): Label-Setting für das Pricing mit Zeitfenstern und Last, mit einstellbarem Gedächtnis gegen Kreise.

Ein Label beschreibt einen Teilweg vom Depot bis zu einem Kunden: [Zeit, Kosten, Last, Gedächtnis (Bitmaske), Kunde, Vorgänger, tot].
Das Gedächtnis entscheidet, welche Wiederholungen verboten sind: k = 1 verbietet nur „Kunde i direkt nach Kunde i“ (Kreise sind erlaubt),
k = n verbietet jede Wiederholung (elementar). Jede Regel ist eine eigene Funktion mit expliziten Ein- und Ausgaben (DEMO-PLAYBOOK 1b):

* `ng_masks`        Gedächtnis-Nachbarschaften (welche Wiederholungen verboten bleiben),
* `extend`          Erweiterungsregel: neuer Kunde, Last, Zeitfenster, Kosten, Gedächtnis,
* `dominiert`       Dominanzregel als Spezifikation (nur zum Prüfen und Erklären; der Kern rechnet dieselbe Regel in `insert_label`),
* `insert_label`    Dominanzprüfung eines neuen Labels gegen alle lebenden Labels am Kunden,
* `trace_route`     Rückverfolgung eines Weges über die Vorgänger,
* `price`           die Komposition: Warteschlange nach Zeit, ruft nur der Reihe nach auf (keine eigene Regel),
* `route_kosten`    reduzierte Kosten einer Route, von Grund auf gerechnet,
* `pruefe_route`    unabhängiger Prüfer einer fertigen Route (Last, Fenster, Horizont, Gedächtnis),
* `aufzaehlung`     Gegenprobe durch Aufzählung aller zulässigen Wege (kleine Instanzen),
* `hat_kreis`, `doppelte_kunden`, `kuerzester_kreis`  Kreise in Routen erkennen.

Messgröße sind erzeugte Labels; Sekunden zählt der Kern nicht. Kein Zustand außerhalb der Argumente; ein Abbruch geschieht nur über die Obergrenze
`max_labels` (deterministisch). Mit ganzen Zahlen oder Brüchen als Dualpreisen und `eps=0` rechnet der Kern exakt (Handbeispiel)."""

import heapq
from dataclasses import dataclass, field

from kip_constants import EPS, NEG_RC


@dataclass
class Ergebnis:
    """Ergebnis eines Pricing-Aufrufs."""

    routen: list                  # [(reduzierte Kosten, Route)], beste zuerst, nur negative reduzierte Kosten
    erzeugt: int                  # erzeugte Labels inklusive des Startlabels
    dominiert: int                # dominierte Labels (neue, die sofort wegfielen, und alte, die ein neues ablöste)
    vergleiche: int               # ausgewertete Dominanztests („O gegen N“ und „N gegen O“ je einmal)
    abgebrochen: bool             # Obergrenze `max_labels` oder `max_vergleiche` erreicht: dann sind die Zahlen unvollständig
    last_geschnitten: int         # Erweiterungen, die an der Kapazität scheiterten (zuerst geprüft)
    fenster_geschnitten: int      # Erweiterungen, die am Zeitfenster scheiterten (nur nach bestandener Lastprüfung)
    ueberlebende: tuple = field(default=())   # je Knoten die lebenden Labels als (Zeit, Kosten, Last)

    @property
    def bester_wert(self):
        """Kleinste reduzierte Kosten aller gefundenen Routen; 0, wenn keine Route negative reduzierte Kosten hat."""
        return self.routen[0][0] if self.routen else 0

    @property
    def anteil_dominiert(self) -> float:
        return self.dominiert / self.erzeugt if self.erzeugt else 0.0


def ng_masks(dist, n: int, k: int) -> list:
    """Gedächtnis-Nachbarschaft NG(j): der Kunde j selbst und seine k − 1 nächsten Kunden (Gleichstand: kleinere Nummer zuerst), als Bitmaske.

    k = 1: nur j selbst, verboten ist nur die sofortige Wiederholung; a-b-a ist erlaubt (Kreise sind erlaubt). k = n: alle, die Route ist elementar."""
    masks = [0] * (n + 1)
    for j in range(1, n + 1):
        andere = sorted((i for i in range(1, n + 1) if i != j), key=lambda i: (dist[j][i], i))
        m = 1 << j
        for i in andere[: max(k - 1, 0)]:
            m |= 1 << i
        masks[j] = m
    return masks


def extend(inst, dual, ng, label, j: int, eps=EPS):
    """Erweiterungsregel: Label am Knoten i um den Kunden j verlängern.

    Rückgabe (neues Label, Grund): Grund ist None, "last" (die Kapazität wäre überschritten; geprüft wird zuerst) oder "fenster"
    (Ankunft nach dem Fensterende). Die Kapazität gilt inklusive (Last = Kapazität ist erlaubt). Warten bis zum Fensteranfang kostet nur Zeit.
    Der Besuch wird jedes Mal gezählt: ein zweiter Besuch am selben Kunden braucht wieder Last, Bedienzeit und Fahrzeit."""
    t, c, q, mem, i = label[0], label[1], label[2], label[3], label[4]
    q2 = q + inst.last[j]
    if q2 > inst.kapazitaet:
        return None, "last"
    ank = t + (inst.bedienzeit if i != 0 else 0) + inst.dist[i][j]
    if ank > inst.spaet[j] + eps:
        return None, "fenster"
    return [max(ank, inst.frueh[j]), c + inst.dist[i][j] - dual[j], q2, (mem & ng[j]) | (1 << j), j, None, False], None


def dominiert(o, n, eps=EPS) -> bool:
    """Dominanzregel (Spezifikation): Label o dominiert Label n am selben Kunden, wenn Kosten, Zeit und Last von o höchstens
    so groß sind wie von n und das Gedächtnis von o eine Teilmenge des Gedächtnisses von n ist."""
    return o[1] <= n[1] + eps and o[0] <= n[0] + eps and o[2] <= n[2] and (o[3] & ~n[3]) == 0


def insert_label(labels, am_knoten, neu, eps=EPS):
    """Dominanzprüfung eines neuen Labels `neu` gegen die lebenden Labels `am_knoten` (Liste von Indizes in `labels`).

    1. Dominiert ein lebendes Label das neue, fällt das neue weg (Abbruch beim ersten Treffer).
    2. Sonst dominiert das neue jedes lebende Label, das es dominieren kann; diese werden tot gesetzt.
    Rückgabe (Index des dominierenden alten Labels oder None, Liste der abgelösten alten Labels, lebende Labels danach ohne das neue, Zahl der Tests)."""
    c2, t2, q2, m2 = neu[1], neu[0], neu[2], neu[3]
    vergleiche = 0
    for oi in am_knoten:
        o = labels[oi]
        if o[6]:
            continue
        vergleiche += 1
        if o[1] <= c2 + eps and o[0] <= t2 + eps and o[2] <= q2 and (o[3] & ~m2) == 0:
            return oi, [], am_knoten, vergleiche
    lebend, abgeloest = [], []
    for oi in am_knoten:
        o = labels[oi]
        if o[6]:
            continue
        vergleiche += 1
        if c2 <= o[1] + eps and t2 <= o[0] + eps and q2 <= o[2] and (m2 & ~o[3]) == 0:
            o[6] = True
            abgeloest.append(oi)
        else:
            lebend.append(oi)
    return None, abgeloest, lebend, vergleiche


def trace_route(labels, li: int) -> tuple:
    """Route (Kundennummern in Besuchsreihenfolge) eines Labels über die Vorgänger."""
    route = []
    while li != -1:
        route.append(labels[li][4])
        li = labels[li][5]
    return tuple(reversed(route))[1:]


def price(inst, dual, k: int, max_routes: int = 15, max_labels=None, max_vergleiche=None, trace=None, eps=EPS, neg=NEG_RC) -> Ergebnis:
    """Pricing: die besten Wege mit negativen reduzierten Kosten bei Gedächtnis k (1 = Kreise erlaubt, n = elementar).

    dual: Dualpreise (Position 0 = Depot = 0); max_routes: so viele Routen mit den kleinsten reduzierten Kosten werden zurückgegeben.
    max_labels, max_vergleiche: Obergrenzen für erzeugte Labels und Dominanztests (None = unbegrenzt); wird eine erreicht, endet die Rechnung und `abgebrochen` ist gesetzt
    (die Zahlen sind dann unvollständig). Beides sind Zählungen, keine Zeitgrenzen: der Abbruch ist reproduzierbar.
    eps: Toleranz der Vergleiche (0 bei ganzen Zahlen oder Brüchen); neg: Schwelle für „negative reduzierte Kosten“ (0 bei exakter Rechnung).
    trace: wenn eine Liste, werden Ereignisse angehängt (nur Beobachtung, ändert nichts):
      ("neu", Id, Vorgänger-Id, Kunde, Zeit, Kosten, Last, dominierende Id oder None)
      ("ersetzt", Id des abgelösten alten Labels, Id des neuen Labels)."""
    n = inst.n
    ng = ng_masks(inst.dist, n, k)
    # Label: [Zeit, Kosten, Last, Gedächtnis, Kunde, Vorgänger, tot]
    labels = [[0, 0, 0, 0, 0, -1, False]]
    am_knoten = [[] for _ in range(n + 1)]
    heap = [(0, 0)]
    erzeugt, dominiert_n, vergleiche = 1, 0, 0
    last_gesch, fenster_gesch = 0, 0
    enden = []
    abgebrochen = False
    if trace is not None:
        trace.append(("neu", 0, -1, 0, 0, 0, 0, None))
    while heap:
        _, li = heapq.heappop(heap)
        lab = labels[li]
        if lab[6]:
            continue
        if (max_labels is not None and erzeugt >= max_labels) or (max_vergleiche is not None and vergleiche >= max_vergleiche):
            abgebrochen = True
            break
        i = lab[4]
        if i != 0 and lab[0] + inst.bedienzeit + inst.dist[i][0] <= inst.horizont + eps:
            enden.append((lab[1] + inst.dist[i][0], li))
        for j in range(1, n + 1):
            if j == i or (lab[3] >> j) & 1:
                continue
            neues, grund = extend(inst, dual, ng, lab, j, eps)
            if neues is None:
                if grund == "last":
                    last_gesch += 1
                else:
                    fenster_gesch += 1
                continue
            neues[5] = li
            erzeugt += 1
            nid = len(labels)
            von, abgeloest, lebend, v = insert_label(labels, am_knoten[j], neues, eps)
            vergleiche += v
            if von is not None:
                dominiert_n += 1
                neues[6] = True
                labels.append(neues)   # die Nummer bleibt vergeben (Nummern = Reihenfolge der Erzeugung); das tote Label wird nie erweitert
                if trace is not None:
                    trace.append(("neu", nid, li, j, neues[0], neues[1], neues[2], von))
                continue
            dominiert_n += len(abgeloest)
            am_knoten[j] = lebend
            labels.append(neues)
            am_knoten[j].append(nid)
            heapq.heappush(heap, (neues[0], nid))
            if trace is not None:
                trace.append(("neu", nid, li, j, neues[0], neues[1], neues[2], None))
                for oi in abgeloest:
                    trace.append(("ersetzt", oi, nid))
    gefunden = {}
    for rc, li in enden:
        route = trace_route(labels, li)
        if rc < neg and route not in gefunden:
            gefunden[route] = rc
    routen = sorted((rc, route) for route, rc in gefunden.items())[:max_routes]
    ueberlebende = tuple(tuple((labels[x][0], labels[x][1], labels[x][2]) for x in am_knoten[j] if not labels[x][6]) for j in range(n + 1))
    return Ergebnis(routen, erzeugt, dominiert_n, vergleiche, abgebrochen, last_gesch, fenster_gesch, ueberlebende)


def route_kosten(inst, dual, route):
    """Reduzierte Kosten einer Route: Weglänge (Depot, Route, Depot) minus die Dualpreise der besuchten Kunden (jeder Besuch zählt); von Grund auf gerechnet."""
    folge = (0,) + tuple(route) + (0,)
    return sum(inst.dist[a][b] for a, b in zip(folge, folge[1:])) - sum(dual[j] for j in route)


def weg_laenge(inst, route):
    """Länge der Route Depot, Route, Depot (die Kosten der Spalte im Master)."""
    folge = (0,) + tuple(route) + (0,)
    return sum(inst.dist[a][b] for a, b in zip(folge, folge[1:]))


def pruefe_route(inst, route, nachbarn=None, eps=EPS):
    """Unabhängiger Prüfer: rechnet Zeiten und Last der Route von Grund auf. Rückgabe None, wenn die Route alle Regeln einhält, sonst der Text der Verletzung.

    Regeln: Kunden 1..n; jede Ankunft höchstens am Fensterende (warten bis zum Fensteranfang ist erlaubt); Last höchstens die Kapazität (jeder Besuch zählt);
    Rückkehr zum Depot bis zum Horizont; Gedächtnis: `nachbarn[j]` = Menge NG(j); eine Wiederholung von j ist nur erlaubt, wenn zwischen den beiden Besuchen
    ein Kunde liegt, dessen Nachbarschaft j nicht enthält (bei k = 1 also nie direkt nacheinander)."""
    folge = tuple(route)
    if not folge:
        return "leere Route"
    t, vorher, q = 0, 0, 0
    for j in folge:
        if not 1 <= j <= inst.n:
            return f"Kunde {j} existiert nicht"
        t = t + (inst.bedienzeit if vorher != 0 else 0) + inst.dist[vorher][j]
        if t > inst.spaet[j] + eps:
            return f"Ankunft {t} bei Kunde {j} nach dem Fensterende {inst.spaet[j]}"
        t = max(t, inst.frueh[j])
        q += inst.last[j]
        if q > inst.kapazitaet:
            return f"Last {q} überschreitet die Kapazität {inst.kapazitaet} bei Kunde {j}"
        vorher = j
    if t + inst.bedienzeit + inst.dist[vorher][0] > inst.horizont + eps:
        return "Rückkehr zum Depot nach dem Horizont"
    if nachbarn is not None:
        for p in range(len(folge)):
            for s in range(p):
                if folge[s] == folge[p] and all(folge[p] in nachbarn[folge[x]] for x in range(s + 1, p)):
                    return f"Kunde {folge[p]} wiederholt, obwohl das Gedächtnis ihn noch kennt"
    return None


def fahrplan(inst, dual, route) -> list:
    """Fahrplan einer zulässigen Route: je Halt Kunde, Entfernung von vorher, Dualpreis, Ankunft, Beginn der Bedienung, Last und Kosten (kumuliert, mit Dualpreisen).

    Wiederholte Besuche stehen als eigene Zeilen mit der Nummer des Besuchs (1, 2, ...); eine unzulässige Route bricht ohne Fehler an der ersten Verletzung ab."""
    zeilen, t, q, vorher, kosten, besuche = [], 0, 0, 0, 0, {}
    for j in route:
        weg = inst.dist[vorher][j]
        ank = t + (inst.bedienzeit if vorher != 0 else 0) + weg
        if ank > inst.spaet[j] + EPS or q + inst.last[j] > inst.kapazitaet:
            break
        t, q = max(ank, inst.frueh[j]), q + inst.last[j]
        kosten += weg - dual[j]
        besuche[j] = besuche.get(j, 0) + 1
        zeilen.append({"kunde": j, "besuch": besuche[j], "entfernung": weg, "dualpreis": dual[j], "ankunft": ank, "beginn": t, "last": q, "kosten": kosten})
        vorher = j
    return zeilen


def alle_routen(inst, elementar: bool, eps=EPS) -> list:
    """Gegenprobe durch Aufzählung (nur für kleine Instanzen): alle zulässigen Routen mit Last, Fenstern und Horizont, ohne Dominanz, in der Reihenfolge der Tiefensuche.

    Verboten ist „Kunde i direkt nach i“ (Kreise erlaubt) oder, bei `elementar`, jede Wiederholung. Tiefensuche über alle Teilwege; jeder Besuch zählt Last und Zeit."""
    routen = []

    def rec(i, t, q, weg):
        if i != 0 and t + inst.bedienzeit + inst.dist[i][0] <= inst.horizont + eps:
            routen.append(tuple(weg))
        for j in range(1, inst.n + 1):
            if j == i or (elementar and j in weg):
                continue
            q2 = q + inst.last[j]
            if q2 > inst.kapazitaet:
                continue
            ank = t + (inst.bedienzeit if i != 0 else 0) + inst.dist[i][j]
            if ank > inst.spaet[j] + eps:
                continue
            rec(j, max(ank, inst.frueh[j]), q2, weg + [j])

    rec(0, 0, 0, [])
    return routen


def aufzaehlung(inst, dual, elementar: bool, eps=EPS):
    """Kennzahlen der Aufzählung aller zulässigen Routen (`alle_routen`) bei den Dualpreisen `dual`.

    Rückgabe (bester Wert, bester Weg, Zahl zulässiger Wege, davon mit Kreis, davon mit negativen reduzierten Kosten);
    bester Wert 0 und leerer Weg, wenn kein Weg negative reduzierte Kosten hat (Gleichstand: kleinere Besuchsfolge)."""
    routen = alle_routen(inst, elementar, eps)
    bewertet = [(route_kosten(inst, dual, r), r) for r in routen]
    negativ = [x for x in bewertet if x[0] < 0]
    bester = min(negativ) if negativ else (0, ())
    return bester[0], bester[1], len(routen), sum(1 for r in routen if hat_kreis(r)), len(negativ)


# ---------------------------------------------------------------------------------------------------------------------------------
# Kreise in Routen
# ---------------------------------------------------------------------------------------------------------------------------------

def hat_kreis(route) -> bool:
    """Besucht die Route einen Kunden mehr als einmal?"""
    return len(set(route)) < len(route)


def doppelte_kunden(route) -> dict:
    """Kunden, die mehrfach besucht werden, mit der Zahl ihrer Besuche."""
    return {j: route.count(j) for j in sorted(set(route)) if route.count(j) > 1}


def wiederholungen(route) -> int:
    """Zahl der Wiederholungen: Länge der Route minus Zahl der verschiedenen Kunden."""
    return len(route) - len(set(route))


def kuerzester_kreis(route):
    """Länge des kürzesten Kreises in Kanten (zwei Besuche desselben Kunden mit k − 1 Kunden dazwischen haben die Länge k; 2 heißt i, j, i); None ohne Kreis."""
    beste, zuletzt = None, {}
    for pos, c in enumerate(route):
        if c in zuletzt:
            m = pos - zuletzt[c]
            beste = m if beste is None else min(beste, m)
        zuletzt[c] = pos
    return beste
