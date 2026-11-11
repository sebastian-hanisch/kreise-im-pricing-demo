"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben.

Beschriftungen stehen als Text auf Kategorienachsen, damit Plotly keine lineare Achse mit Zwischenwerten anlegt; die Wertachsen haben feste Bereiche."""

import plotly.graph_objects as go

import kip_constants as C
from kip_evaluation import fmt_dec, fmt_int, fmt_pct

REGEL_KREISE = "Kreise erlaubt (k = 1)"
REGEL_ELEMENTAR = "elementar"


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=330, legende=True):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), plot_bgcolor="rgba(0,0,0,0)",
                      legend=dict(orientation="h", y=-0.25) if legende else None, showlegend=legende)
    return lock_axes(fig)


def build_labels_hand(z1: dict, ze: dict):
    """Erzeugte Labels am Handbeispiel (ein Pricing-Aufruf), gestapelt in lebende (bleiben) und dominierte (fallen weg); mit erlaubten Kreisen und elementar."""
    xs = [REGEL_KREISE, REGEL_ELEMENTAR]
    zs = [z1, ze]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=xs, y=[z["erzeugt"] - z["dominiert"] for z in zs], name="bleiben", marker_color=C.COLOR_KEPT, hovertemplate="%{x}: %{y} Labels bleiben<extra></extra>"))
    fig.add_trace(go.Bar(x=xs, y=[z["dominiert"] for z in zs], name="dominiert (fallen weg)", marker_color=C.COLOR_DOMINATED, hovertemplate="%{x}: %{y} Labels dominiert<extra></extra>"))
    hoehe = max(z["erzeugt"] for z in zs)
    for z, x in zip(zs, xs):
        fig.add_annotation(x=x, y=z["erzeugt"], text=f"{fmt_int(z['erzeugt'])} erzeugt", showarrow=False, yshift=12, font=dict(size=11))
    fig.update_layout(barmode="stack")
    fig.update_yaxes(title_text="erzeugte Labels", range=[0, hoehe * 1.2])
    return _base(fig)


def build_master_verlauf(werte_k1: list, werte_el: list):
    """Wert des Masters je Runde der Spaltenerzeugung im Handbeispiel (Linie je Regel); die Werte sind exakt gerechnet und hier als Gleitkommazahlen gezeichnet."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[f"Runde {i}" for i in range(1, len(werte_k1) + 1)], y=[float(w) for w in werte_k1], mode="lines+markers", name=REGEL_KREISE,
                             line=dict(color=C.COLOR_LINE2, width=3), hovertemplate="%{x}: %{y:.2f}<extra>" + REGEL_KREISE + "</extra>"))
    fig.add_trace(go.Scatter(x=[f"Runde {i}" for i in range(1, len(werte_el) + 1)], y=[float(w) for w in werte_el], mode="lines+markers", name=REGEL_ELEMENTAR,
                             line=dict(color=C.COLOR_LINE, width=3), hovertemplate="%{x}: %{y:.2f}<extra>" + REGEL_ELEMENTAR + "</extra>"))
    hoch = max(float(max(werte_k1)), float(max(werte_el)))
    fig.update_yaxes(title_text="Wert des Masters (untere Schranke der Runde)", range=[0, hoch * 1.1])
    return _base(fig)


def build_live_labels(z: dict):
    """Erzeugte Labels der ganzen Spaltenerzeugung (alle Pricing-Aufrufe zusammen) mit erlaubten Kreisen und elementar; bei Abbruch der elementaren Rechnung nur bis zur Obergrenze."""
    k1, el = z["k1"], z["elem"]
    xs = [REGEL_KREISE, REGEL_ELEMENTAR + (" (abgebrochen)" if el["abgebrochen"] else "")]
    ys = [k1["labels"], el["labels"]]
    fig = go.Figure(go.Bar(x=xs, y=ys, marker_color=[C.COLOR_LINE2, C.COLOR_DOMINATED if el["abgebrochen"] else C.COLOR_LINE], text=[fmt_int(y) for y in ys], textposition="outside",
                           hovertemplate="%{x}: %{y} Labels<extra></extra>"))
    fig.update_yaxes(title_text="erzeugte Labels (alle Pricing-Aufrufe)", range=[0, max(ys) * 1.25 if max(ys) else 1])
    return _base(fig, legende=False)


def build_kreislaengen(live: dict, fest: dict):
    """Anteil der Kreis-Spalten nach kürzestem Kreis (zwei, drei, vier oder mehr Kanten): die gewählte Instanz und die feste Messreihe der gleichen Breite."""
    kategorien = ["2", "3", "4+"]
    namen = {"2": "zwei Kanten (i, j, i)", "3": "drei Kanten", "4+": "vier oder mehr"}
    fig = go.Figure()
    for name, kz, farbe in (("diese Instanz", live, C.COLOR_LINE2), (f"feste Messreihe ({fest['instanzen']} Instanzen)", fest, C.COLOR_LINE)):
        gesamt = kz["mit_kreis"]
        ys = [100 * kz["kuerzeste"][k] / gesamt if gesamt else 0 for k in kategorien]
        fig.add_trace(go.Bar(x=[namen[k] for k in kategorien], y=ys, name=name, marker_color=farbe, text=[fmt_dec(y) + " %" if y else "" for y in ys], textposition="outside",   # Balken der Höhe 0 ohne Beschriftung (Plotly meldet sonst NaN-Positionen in der Konsole)
                             
                             hovertemplate="%{x}: %{y:.1f} %<extra>" + name + "</extra>"))
    fig.update_layout(barmode="group")
    fig.update_yaxes(title_text="Anteil der Kreis-Spalten (%)", range=[0, 118])
    return _base(fig)


def build_wiederholungen(live: dict, fest: dict):
    """Zahl der Wiederholungen je Kreis-Spalte (1, 2, 3 und mehr): Anteil der Kreis-Spalten, gewählte Instanz und feste Messreihe."""
    def gruppiert(w):
        out = {"eine Wiederholung": 0, "zwei": 0, "drei und mehr": 0}
        for k, v in w.items():
            out["eine Wiederholung" if int(k) == 1 else "zwei" if int(k) == 2 else "drei und mehr"] += v
        return out
    fig = go.Figure()
    for name, kz, farbe in (("diese Instanz", live, C.COLOR_LINE2), (f"feste Messreihe ({fest['instanzen']} Instanzen)", fest, C.COLOR_LINE)):
        g = gruppiert(kz["wiederholungen"])
        gesamt = sum(g.values())
        ys = [100 * v / gesamt if gesamt else 0 for v in g.values()]
        fig.add_trace(go.Bar(x=list(g), y=ys, name=name, marker_color=farbe, text=[fmt_dec(y) + " %" if y else "" for y in ys], textposition="outside",   # Balken der Höhe 0 ohne Beschriftung (Plotly meldet sonst NaN-Positionen in der Konsole)
                             
                             hovertemplate="%{x}: %{y:.1f} %<extra>" + name + "</extra>"))
    fig.update_layout(barmode="group")
    fig.update_xaxes(title_text="Wiederholungen je Kreis-Spalte (Länge minus verschiedene Kunden)", type="category")
    fig.update_yaxes(title_text="Anteil der Kreis-Spalten (%)", range=[0, 118])
    return _base(fig)


def build_kreisanteil(tabelle: list):
    """Anteil der Spalten mit Kreis je Fensterbreite: unter den neuen Spalten, unter den Spalten der Endlösung und an der Menge der Endlösung."""
    xs = [f"Breite {z['breite']}" for z in tabelle]
    fig = go.Figure()
    for name, schluessel, farbe in (("neue Spalten", "anteil_neue", C.COLOR_LINE2), ("Spalten der Endlösung", "anteil_ende", C.COLOR_LINE3), ("Menge der Endlösung", "anteil_menge", C.COLOR_LINE4)):
        ys = [100 * z[schluessel] for z in tabelle]
        fig.add_trace(go.Bar(x=xs, y=ys, name=name, marker_color=farbe, text=[fmt_pct(z[schluessel]) for z in tabelle], textposition="outside",
                             hovertemplate="%{x}: %{y:.1f} %<extra>" + name + "</extra>"))
    fig.update_layout(barmode="group")
    fig.update_yaxes(title_text="Anteil mit Kreis (%)", range=[0, 118])
    return _base(fig)


def build_luecke(zeilen: list):
    """Mittlere Lücke der Schranke zur elementaren je Zahl der Kunden, eine Linie je Fensterbreite; Quadrate zeigen das Maximum über die Instanzen."""
    fig = go.Figure()
    farben = {40: C.COLOR_LINE, 100: C.COLOR_LINE2}
    for breite in sorted({z["breite"] for z in zeilen}):
        zs = sorted((z for z in zeilen if z["breite"] == breite and z["mittel"] is not None), key=lambda z: z["n"])
        xs = [f"n = {z['n']}" for z in zs]
        fig.add_trace(go.Scatter(x=xs, y=[100 * z["mittel"] for z in zs], mode="lines+markers", name=f"Breite {breite}: Mittel", line=dict(color=farben.get(breite, C.COLOR_LINE3), width=3),
                                 hovertemplate="%{x}: %{y:.2f} %<extra>Breite " + str(breite) + ", Mittel</extra>"))
        fig.add_trace(go.Scatter(x=xs, y=[100 * z["maximum"] for z in zs], mode="markers", name=f"Breite {breite}: Maximum", marker=dict(color=farben.get(breite, C.COLOR_LINE3), symbol="square-open", size=9),
                                 hovertemplate="%{x}: %{y:.2f} %<extra>Breite " + str(breite) + ", Maximum</extra>"))
    fig.update_yaxes(title_text="Lücke zur elementaren Schranke (%)", range=[0, 15])
    return _base(fig)
