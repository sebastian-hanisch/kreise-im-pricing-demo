"""Längere Texte der App, die auch in der README stehen (ein Test vergleicht beide Fassungen) und der Formel-Expander.

Zahlen im Text kommen aus den festen Messreihen (`kip_baender`) und den Konstanten, nicht aus dem Kopf."""

import kip_baender as B
import kip_constants as C
from kip_evaluation import NBSP, fmt_dec, fmt_int


def assumptions_markdown() -> str:
    """Annahmen, Grenzen und bekannte Probleme (App-Expander und README-Abschnitt „Annahmen, Grenzen und bekannte Probleme“)."""
    return f"""**Annahmen**

- Die Instanzen sind eigene, Solomon-artige Instanzen (Quadrat 100 × 100, Zeit = Entfernung, Bedienzeit {int(C.BEDIENZEIT)}, Horizont {int(C.HORIZONT)}, Kapazität {C.KAPAZITAET}, Nachfrage {C.LAST_MIN} bis {C.LAST_MAX}), zufällig verteilt, nicht die Originalinstanzen von Solomon. Das Handbeispiel hat sieben Kunden, ganzzahlige Entfernungen (Manhattan-Abstand), Bedienzeit 2, Kapazität 6 und Rückkehr bis 38.
- „Kreise erlaubt“ heißt: Verboten ist nur, denselben Kunden direkt nacheinander zu besuchen (Gedächtnis k = 1); sonst darf ein Kunde mehrfach vorkommen. Jeder Besuch zählt Last, Bedienzeit, Fahrzeit und Dualpreis erneut. „Elementar“ heißt: jeder Kunde höchstens einmal.
- Der Master ist ein Überdeckungs-Master (jeder Kunde mindestens einmal überdeckt); eine Spalte mit Kreis zählt einen mehrfach besuchten Kunden mehrfach. Gerechnet wird mit HiGHS (Zufallsinstanzen) und im Handbeispiel exakt mit Brüchen. Je Runde kommen bei Zufallsinstanzen bis zu {C.MAX_NEUE_SPALTEN} neue Spalten dazu, im Handbeispiel genau eine.
- Dualpreise sind die Preise, die der Master je Kunde vorgibt. In Experiment 1 sind es die Preise der ersten Runde (Hin- und Rückweg vom Depot, nur der von Kunde 7 ist einstellbar); in den Experimenten 2 bis 5 entstehen sie Runde für Runde aus dem Master.
- Gezählt werden erzeugte Labels und Dominanztests; Sekunden stehen nur zur Information da.

**Grenzen**

- Die festen Messreihen haben je Zelle 5 oder 6 Instanzen (Zufalls-Seeds ab 0), kein Konfidenzmaß; nur die Zeilen mit Bezug k = 16 haben 12 Instanzen.
- Gerechnet sind: der Anteil der Spalten mit Kreis bei n = 30 (Fensterbreite 40, 100 und 200); die Lücke zur elementaren Schranke bei n = 10 bis 30 (Breite 40 und 100, zufällig verteilt); die Lücke zur Schranke bei k = 8 bei n = 30 (zufällig, gruppiert und lang, je 5 Instanzen). Nicht gemessen sind die Lücke zur elementaren Schranke bei Breite 200, bei gruppierten und langen Instanzen und bei mehr als 30 Kunden.
- Die Zeilen mit Bezug k = 16 (n = 50 und 100) stammen nur aus einer Auswertungsdatei der Messungen vor dem Bau und sind mit dem Kern dieser Demo nicht neu gerechnet. Ein Bezug k = 8 oder k = 16 ist nicht die elementare Schranke: die Schranke sinkt mit wachsendem k nie (im Test an kleinen Instanzen nachgeprüft; sie steigt mit k), also ist die Lücke zu k = 8 oder 16 höchstens so groß wie die zur elementaren Schranke.
- Gezeigt wird nur der Preis der Kreise (die tiefere Schranke) und wie oft sie vorkommen; Verfahren, die Kreise teilweise oder ganz verbieten, sind außer der elementaren Rechnung nicht Gegenstand dieser Demo.
- Nur Vorwärts-Labeling und nur der Überdeckungs-Master.

**Bekannte Probleme und Unsicherheiten**

- Die elementare Rechnung der Live-Rechnung bricht an einer festen Obergrenze ab ({fmt_int(C.LIVE_MAX_VERGLEICHE_ELEMENTAR)} Dominanztests in allen Pricing-Aufrufen zusammen); dann gibt es für diese Einstellung keine elementare Schranke und keine Lücke. Die Obergrenze zählt, sie misst keine Sekunden.
- Die Zahl der Spalten, der Runden und der Spalten mit Kreis hängt von den Dualpreisen des Master-Lösers ab: gibt es mehrere gleich gute Lösungen, kann HiGHS auf einem anderen Rechner andere Dualpreise liefern. Der Wert der Schranke hängt nicht davon ab (er ist der Wert der linearen Relaxation über alle zulässigen Routen). Die festen Messreihen sind auf einem Windows-Rechner gerechnet.
- Die Instanzen entstehen mit dem Zufallsgenerator von Python (`random.Random`), damit sie mit den festen Messreihen übereinstimmen; Stichproben der Messreihen werden in den Tests nachgerechnet.
- Erklärungen mit „weil“ sind Deutungen, soweit nicht ausdrücklich gemessen (zum Beispiel, warum bei engen Fenstern kaum Kreise vorkommen).
- Die Diagramme haben keine Auswahlfunktion; ein Mausklick auf sie bewirkt nichts."""


MATH_LESEHILFE = r"""**Lesehilfe.** *Gegeben:* ein Depot und $n$ Kunden mit Entfernungen (gleich Fahrzeiten), Zeitfenstern, Lasten und Dualpreisen. *Gesucht:* die Route mit den kleinsten reduzierten Kosten, wenn ein Kunde mehrfach vorkommen darf (nur derselbe Kunde direkt nacheinander ist verboten), und die untere Schranke, bei der die Spaltenerzeugung dann endet, im Vergleich zur elementaren Schranke.

| Symbol | Bedeutung |
|---|---|
| $0, 1, \dots, n$ | Depot und Kunden |
| $d_{ij}$ | Entfernung von $i$ nach $j$ (gleich der Fahrzeit) |
| $s$, $H$ | Bedienzeit je Besuch (nicht am Depot), spätester Rückkehrzeitpunkt am Depot |
| $[e_j, l_j]$ | Zeitfenster des Kunden $j$ |
| $q_j$, $Q$ | Last des Kunden $j$, Kapazität des Fahrzeugs |
| $\pi_j$ | Dualpreis des Kunden $j$ (Preis, den der Master je Kunde vorgibt) |
| $r = (j_1, \dots, j_m)$ | Route: Besuchsfolge der Kunden, $j_p \ne j_{p+1}$; ein Kunde darf mehrfach vorkommen |
| $a_{jr}$ | Zahl der Besuche des Kunden $j$ in der Route $r$ |
| $c_r$ | Kosten der Route (Weglänge Depot, Route, Depot) |
| $\bar c_r$ | reduzierte Kosten der Route |
| $N_j$ | Gedächtnis-Nachbarschaft des Kunden $j$ (bei $k = 1$ nur $j$ selbst, bei $k = n$ alle Kunden) |
| $z_k$ | Schranke der Spaltenerzeugung bei Gedächtnis $k$ |
"""

MATH_FORMELN = r"""**Reduzierte Kosten.** Jeder Besuch bringt seinen Dualpreis ein, auch ein wiederholter Besuch desselben Kunden:

$$\bar c_r = c_r - \sum_{p=1}^{m} \pi_{j_p}, \qquad c_r = d_{0 j_1} + \sum_{p=1}^{m-1} d_{j_p j_{p+1}} + d_{j_m 0}.$$

**Zulässige Route.** Mit $t_1 = \max(d_{0 j_1}, e_{j_1})$ und $t_{p+1} = \max(t_p + s + d_{j_p j_{p+1}}, e_{j_{p+1}})$ muss jede Ankunft im Fenster liegen ($t_p + s + d_{j_p j_{p+1}} \le l_{j_{p+1}}$ und $d_{0 j_1} \le l_{j_1}$), die Last aller Besuche (jeder Besuch zählt) höchstens $Q$ sein, und die Rückkehr bis $H$ klappen:

$$\sum_{p=1}^{m} q_{j_p} \le Q, \qquad t_m + s + d_{j_m 0} \le H.$$

**Master und Schranke.** Der Überdeckungs-Master über alle bisher bekannten Routen und sein Duales:

$$\min \sum_r c_r x_r \;\; \text{mit} \;\; \sum_r a_{jr} x_r \ge 1 \;\;(j = 1, \dots, n), \; x \ge 0, \qquad \max \sum_j \pi_j \;\; \text{mit} \;\; \sum_j a_{jr} \pi_j \le c_r \;\;(\text{alle } r), \; \pi \ge 0.$$

Findet das Pricing keine zulässige Route der gewählten Regel mit $\bar c_r < 0$, ist der Wert des Masters die Schranke $z_k$: der Wert der linearen Relaxation über alle zulässigen Routen dieser Regel. Eine Route mit Kreis ist für $k = 1$ zulässig, für $k = n$ nicht. Jede elementare Route ist auch bei $k = 1$ zulässig; deshalb gilt $z_1 \le z_n$. Die Lücke ist

$$\text{Lücke} = \frac{z_n - z_1}{z_n}.$$

**Label und Dominanz.** Ein Label $\ell = (t, c, q, M)$ am Kunden $i$ steht für einen Teilweg: Zeit, reduzierte Kosten, Last, Gedächtnis (Menge). Es wird um den Kunden $j \notin M$ verlängert, wenn Fenster und Kapazität halten; das neue Label hat

$$t' = \max(t + s\,[i \ne 0] + d_{ij},\, e_j), \qquad c' = c + d_{ij} - \pi_j, \qquad q' = q + q_j, \qquad M' = (M \cap N_j) \cup \{j\}.$$

Ein Label $\ell$ dominiert ein Label $\ell'$ am selben Kunden, wenn

$$c \le c', \qquad t \le t', \qquad q \le q', \qquad M \subseteq M'.$$

*Warum das richtig ist:* Jede Fortsetzung, die für $\ell'$ zulässig ist, ist auch für $\ell$ zulässig (Zeit und Last von $\ell$ sind nicht größer, das Gedächtnis verbietet nicht mehr), und beide sammeln dieselben Kostenzuwächse. Bei $k = 1$ ist $M = \{i\}$ für jedes Label am Kunden $i$, die Gedächtnisbedingung ist immer erfüllt: die Dominanz vergleicht nur Kosten, Zeit und Last. Bei $k = n$ enthält $M$ alle besuchten Kunden, und die Bedingung $M \subseteq M'$ kommt hinzu.

**Warum die erste Runde Kreise anzieht (Rechnung, keine Messung).** In der ersten Runde sind die Startspalten die Einzelfahrten, ihre Kosten sind die Dualpreise: $\pi_i = 2 d_{0i}$. Für die Route $0, i, j, 0$ gilt dann $\bar c = d_{0i} + d_{ij} + d_{j0} - 2 d_{0i} - 2 d_{0j} = d_{ij} - d_{0i} - d_{0j}$, für die Route $0, i, j, i, 0$ dagegen

$$\bar c = 2 d_{0i} + 2 d_{ij} - (2\pi_i + \pi_j) = 2\,(d_{ij} - d_{0i} - d_{0j}).$$

Der Weg mit Kreis hat also genau die doppelten reduzierten Kosten, sofern Last und Zeitfenster beide Besuche von $i$ erlauben.

**Literatur.** Dass in vielen Fällen schon die nichtelementare Relaxation brauchbare Optima liefert, bei anderen Problemen aber nicht, steht laut Zusammenfassung bei Feillet, Dejax, Gendreau und Gueguen (2004), *Networks* 44(3):216–229; nur die Zusammenfassung wurde eingesehen, der Volltext nicht. Die Zustandsraum-Relaxation, aus der solche Schranken stammen, geht auf Christofides, Mingozzi und Toth (1981), *Networks* 11(2):145–164, zurück (ebenfalls nur die Zusammenfassung eingesehen). Keine Zahl dieser Demo stammt aus der Literatur, und die Sätze der Literatur sind nur ein Vergleich, kein Beleg für die Messungen hier."""


def annahmen_tabelle() -> str:
    """Tabelle „Wo die Annahmen enden“ der App (Annahme, was gilt, wenn sie nicht gilt, Stand); die Zahlen kommen aus den festen Messreihen."""
    k8 = {z["typ"]: z["mittel"] for z in B.luecke_k8_tabelle()}
    k16 = {(z["typ"], z["n"], z["breite"]): z["mittel"] for z in B.luecke_k16_tabelle()}

    def spanne(n, breite):
        werte = [v for (typ, nn, bb), v in k16.items() if nn == n and bb == breite]
        return f"{fmt_dec(100 * min(werte), 3)} bis {fmt_dec(100 * max(werte), 3)}{NBSP}%"
    return f"""| Annahme | Wenn sie nicht gilt | Stand |
|---|---|---|
| **Zufällig verteilte Instanzen** (Lücke zur elementaren Schranke) | Gruppierte und lange Instanzen sind nur gegen k = 8 gemessen: mittlere Lücke {fmt_dec(100 * k8['cluster'], 2)}{NBSP}% (gruppiert) und {fmt_dec(100 * k8['lang'], 2)}{NBSP}% (lang) gegen {fmt_dec(100 * k8['zufall'], 2)}{NBSP}% (zufällig), je 5 Instanzen. | teilweise gemessen |
| **Fensterbreite 40 bis 200** | Bei Breite 200 ist die elementare Schranke bei n = 30 nicht gerechnet. Bei Breite 20 und n = 100 ist die Lücke zu k = 16 in 12 von 12 Instanzen null, bei beiden Instanztypen (aus der Auswertungsdatei, nicht neu gerechnet). | teilweise gemessen |
| **n bis 30 für die Lücke zur elementaren Schranke** | Bei n = 50 und n = 100 nur gegen k = 16 (nicht neu gerechnet): mittlere Lücke bei n = 50, Breite 40: {spanne(50, 40)}, Breite 100: {spanne(50, 100)}; bei n = 100, Breite 40: {spanne(100, 40)} (je zwei Instanztypen, 12 Instanzen). | teilweise gemessen |
| **Dualpreise Runde für Runde aus dem Master (Überdeckung)** | Andere Master (Partitionierung) und geglättete Dualpreise sind nicht gerechnet. | nicht gemessen |
| **Kreise erlaubt = nur die direkte Wiederholung verboten** | Verfahren, die Kreise teilweise oder ganz verbieten (größeres Gedächtnis), werden nur über die elementare Rechnung als Gegenpol gezeigt. | nicht Gegenstand |
"""
