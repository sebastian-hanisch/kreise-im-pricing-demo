"""Konstanten: Regler-Grenzen, feste Annahmen, Farben und Presets.

Rechenaufwand am Regler-Maximum (DEMO-PLAYBOOK 1c): Die Live-Rechnung (Experiment 3) führt die ganze Spaltenerzeugung aus, einmal mit Kreisen
(Gedächtnis k = 1, wenige Labels) und einmal elementar (jeder Kunde höchstens einmal, viele Labels). Die elementare Rechnung wächst am schnellsten:
bei n = 20 und Fensterbreite 200 erzeugt sie die meisten Labels. Deshalb ist sie auf LIVE_MAX_VERGLEICHE_ELEMENTAR Dominanztests in allen Pricing-Aufrufen
zusammen begrenzt (feste Zahl statt Zeitgrenze, damit der Abbruch reproduzierbar ist); bei Abbruch zeigt die App „elementar nicht erreicht“ statt einer Zahl.
Größere Fälle stehen als feste Messreihen in data/.
"""

# ---------------------------------------------------------------------------------------------------------------------------------
# Instanz (Solomon-artig, nicht die Originalinstanzen): Quadrat 100 x 100, Zeit = Entfernung, Depot in der Mitte
# ---------------------------------------------------------------------------------------------------------------------------------
HORIZONT = 300.0          # spätester Rückkehrzeitpunkt zum Depot
BEDIENZEIT = 10.0         # je Besuch
KAPAZITAET = 70           # Ladekapazität des Fahrzeugs
LAST_MIN, LAST_MAX = 5, 25   # Nachfrage (Last) je Kunde, ganze Zahlen
EPS = 1e-9                # Toleranz bei Vergleichen von Zeit und Kosten (Gleitkomma)
NEG_RC = -1e-7            # eine Route zählt als Spalte, wenn ihre reduzierten Kosten unter dieser Schwelle liegen
MENGE_EPS = 1e-9          # eine Spalte zählt in der Endlösung, wenn ihre Menge über dieser Rauschgrenze liegt
MAX_NEUE_SPALTEN = 15     # höchstens so viele neue Spalten je Runde (die besten nach reduzierten Kosten)

# Handbeispiel (Experimente 1 und 2): Depot und sieben Kunden, ganze Zahlen
HAND_DUAL7_MIN, HAND_DUAL7_MAX, HAND_DEFAULT_DUAL7 = 2, 14, 10
HAND_RUNDE_MIN, HAND_RUNDE_MAX, HAND_DEFAULT_RUNDE = 1, 8, 1
HAND_REGELN = ("Kreise erlaubt (k = 1)", "elementar (jeder Kunde höchstens einmal)")

# Live-Rechnung (Experiment 3)
LIVE_N_MIN, LIVE_N_MAX, LIVE_DEFAULT_N = 5, 20, 15
LIVE_BREITEN = (20, 40, 60, 100, 200)       # Breite der Zeitfenster
LIVE_DEFAULT_BREITE = 100
SEED_MAX, LIVE_DEFAULT_SEED = 999999, 0
LIVE_MAX_VERGLEICHE_ELEMENTAR = 30_000_000   # Abbruch der elementaren Live-Rechnung: Dominanztests in allen Pricing-Aufrufen zusammen

# ---------------------------------------------------------------------------------------------------------------------------------
# Feste Messreihen (data/): Zufalls-Seeds 0 bis 5 (V7: 0 bis 4)
# ---------------------------------------------------------------------------------------------------------------------------------
BAND_FILE_KREISE = "baender_kreise.json"
BAND_FILE_LUECKE = "baender_luecke.json"

# ---------------------------------------------------------------------------------------------------------------------------------
# Farben (hell und dunkel lesbar)
# ---------------------------------------------------------------------------------------------------------------------------------
COLOR_KEPT = "#2F6B65"
COLOR_DOMINATED = "rgba(150,150,150,0.65)"
COLOR_LINE = "#4c78a8"
COLOR_LINE2 = "#e45756"
COLOR_LINE3 = "#f58518"
COLOR_LINE4 = "#72b7b2"

# ---------------------------------------------------------------------------------------------------------------------------------
# Presets (Schnellstart): jedes setzt ALLE Regler
# ---------------------------------------------------------------------------------------------------------------------------------
_BASIS = {
    "h_regel": HAND_REGELN[0], "h_dual7": HAND_DEFAULT_DUAL7, "h_runde": HAND_DEFAULT_RUNDE,
    "l_n": LIVE_DEFAULT_N, "l_breite": LIVE_DEFAULT_BREITE, "l_seed": LIVE_DEFAULT_SEED,
}
PRESETS = {
    "Grundfall: der Kreis im Handbeispiel": dict(_BASIS),
    "Kreis über Kunde 7 lohnt sich nicht": {**_BASIS, "h_dual7": 2},
    "Enge Fenster (Breite 20)": {**_BASIS, "l_n": 20, "l_breite": 20},
    "Breite 40: Kreise ohne Lücke": {**_BASIS, "l_n": 20, "l_breite": 40},
    "Weite Fenster (Breite 200)": {**_BASIS, "h_runde": HAND_RUNDE_MAX, "l_n": 12, "l_breite": 200},
    "Größte Einstellung (n = 20, Breite 200)": {**_BASIS, "l_n": LIVE_N_MAX, "l_breite": 200},
}
PRESET_HELP = {
    "Grundfall: der Kreis im Handbeispiel": "Handbeispiel mit Dualpreis 10 für Kunde 7 (sein Wert der ersten Runde): die Experimente 1 und 2 zeigen den Kreis 7 → 6 → 7 → 6. Live-Rechnung mit 15 Kunden und Fensterbreite 100.",
    "Kreis über Kunde 7 lohnt sich nicht": "Handbeispiel mit Dualpreis 2 für Kunde 7: ein Kreis über Kunde 7 lohnt sich gegenüber dem besten elementaren Weg nicht mehr; ein anderer Kreis (über Kunde 5) hat trotzdem die kleinsten reduzierten Kosten. Live-Rechnung wie im Grundfall.",
    "Enge Fenster (Breite 20)": "Live-Rechnung mit 20 Kunden und Fensterbreite 20: in diesem Beispiel (eine Instanz) enthält keine neue Spalte einen Kreis, und die Schranke ist gleich der elementaren.",
    "Breite 40: Kreise ohne Lücke": "Live-Rechnung mit 20 Kunden und Fensterbreite 40: in diesem Beispiel (eine Instanz) enthalten Spalten einen Kreis, und die Schranke liegt trotzdem nicht unter der elementaren.",
    "Weite Fenster (Breite 200)": "Live-Rechnung mit 12 Kunden und Fensterbreite 200, im Handbeispiel die letzte Runde der Spaltenerzeugung: in diesem Beispiel (eine Instanz) enthalten die meisten neuen Spalten einen Kreis.",
    "Größte Einstellung (n = 20, Breite 200)": "Größte Einstellung der Live-Rechnung: 20 Kunden, Fensterbreite 200. Die elementare Rechnung bricht in diesem Beispiel an der Obergrenze ab, es gibt keine Lücke; rechnet einige Sekunden.",
}
