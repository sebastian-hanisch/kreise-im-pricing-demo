"""Kreise im Pricing – interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Wie oft entstehen im Pricing Spalten mit Kreis, wenn Kunden mehrfach besucht werden dürfen, und was kostet das an Schärfe der unteren Schranke?
Handbeispiel Schritt für Schritt, Live-Rechnung, Kreislängen und feste Messreihen.

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import kip_algorithm as A
import kip_baender as B
import kip_constants as C
import kip_evaluation as E
import kip_scenario as S
import kip_texte as T
import kip_visualization as V
from kip_layout import dunkles_design, kopf_css
from kip_presets import (
    bounds,
    choices,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)

st.set_page_config(page_title="Kreise im Pricing – Sebastian Hanisch", layout="wide")


# --- Zwischenspeicher: alle Eingaben stehen im Schlüssel ----------------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def _hand_kreis(dual7):
    return E.hand_kreis(dual7)


@st.cache_data(show_spinner=False)
def _hand_protokoll(regel, dual7):
    _res, prot = E.hand_lauf(E.hand_k(regel), dual7, mit_protokoll=True)
    return E.label_tabelle(prot)


@st.cache_data(show_spinner=False)
def _hand_colgen(elementar):
    return E.hand_spaltenerzeugung(elementar)


@st.cache_data(show_spinner=False)
def _hand_gegenprobe(elementar):
    return E.hand_gegenprobe(elementar)


@st.cache_data(show_spinner=False, max_entries=60)
def _live(n, breite, seed):
    return E.live_lauf(n, breite, seed)


# --- kleine Hilfen für Tabellen -----------------------------------------------------------------------------------------------------------

PROZENT = st.column_config.NumberColumn(format="%.1f %%")
PROZENT2 = st.column_config.NumberColumn(format="%.2f %%")
PROZENT3 = st.column_config.NumberColumn(format="%.3f %%")
GANZ = st.column_config.NumberColumn(format="%d")


def _prozent(x):
    return None if x is None else 100 * x


def _fahrplan_tabelle(inst, dual, route):
    zeilen = []
    for z in A.fahrplan(inst, dual, route):
        zeilen.append({"Halt": f"Kunde {z['kunde']}" + (f" ({z['besuch']}. Besuch)" if z["besuch"] > 1 else ""), "Entfernung von vorher": z["entfernung"], "Dualpreis": E.fmt_wert(z["dualpreis"]),
                       "Ankunft": z["ankunft"], "Beginn der Bedienung": z["beginn"], "Last": z["last"], "Kosten bis hier": E.fmt_wert(z["kosten"])})
    return zeilen


# --- Kopf und Einleitung ------------------------------------------------------------------------------------------------------------------

st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🔁 Kreise im Pricing: wie oft, und was kosten sie?")
st.markdown(
    """
Im **Pricing** der Spaltenerzeugung (zum Beispiel bei der Tourenplanung) sucht das **Label-Setting** die günstigste Route zu den **Dualpreisen**, die der Master je Kunde vorgibt. Eine Route heißt **elementar**, wenn jeder Kunde höchstens einmal vorkommt;
das zu erzwingen ist aufwendig. Eine Möglichkeit ist deshalb, **Kreise** zuzulassen: ein Kunde darf mehrfach vorkommen, nur „Kunde i direkt nach Kunde i“ ist verboten. In den Messreihen mit Zufallsinstanzen braucht das weniger Labels (im kleinen Handbeispiel nicht), aber die **untere Schranke** der Spaltenerzeugung liegt tiefer als die elementare oder gleich hoch.
Diese Demo fragt: **Wie oft enthalten neue Spalten einen Kreis, und wie viel tiefer liegt die Schranke?** Gemessen werden die **erzeugten Labels**, der **Anteil der Spalten mit Kreis** und die **Lücke** der Schranke zur elementaren; Sekunden stehen nur zur Information da.

Weiter unten: fünf Abschnitte **🔬 Experiment**, dann **🚧 Wo die Annahmen enden** und die Expander **⚠️ Annahmen, Grenzen und bekannte Probleme** und **📐 Mathematische Formulierung**.
"""
)

with st.expander("So funktioniert das Pricing mit Kreisen", expanded=True):
    st.markdown(
        """
1. **Aufgabe:** Ein Fahrzeug startet am Depot, besucht Kunden (Zeitfenster, Last) und kehrt zurück. Jede mögliche Route ist eine **Spalte** des **Masters**; der Master gibt je Kunde einen **Dualpreis** vor. Das Pricing sucht die Route mit den kleinsten **reduzierten Kosten**:
   Weglänge minus die Dualpreise der besuchten Kunden. Hat sie negative reduzierte Kosten, kommt sie als neue Spalte in den Master. Die Schleife endet, wenn es keine solche Route mehr gibt; der Wert des Masters ist dann die **Schranke** (eine untere Grenze für den Wert der Lösung).
2. **Kreis:** Die Route 7 → 6 → 7 → 6 besucht Kunde 7 und Kunde 6 je zweimal. **Jeder Besuch** zählt Last, Bedienzeit, Fahrzeit und Dualpreis erneut. Ein zweiter Besuch lohnt sich, wenn der Dualpreis des Kunden größer ist als der Umweg, den er kostet, und Last und Zeitfenster ihn erlauben.
3. **Gedächtnis:** Jedes Label (ein Teilweg samt Kosten, Zeit und Last) merkt sich nur den zuletzt besuchten Kunden (k = 1): dann ist nur die direkte Wiederholung verboten, Kreise sind erlaubt. Elementar muss sich jedes Label **alle** besuchten Kunden merken; zwei Labels sind dann nur vergleichbar, wenn das eine nicht mehr Kunden kennt als das andere.
4. **Der Preis:** Mit Kreisen sind mehr Routen zulässig als elementar. Die Schranke ist der Wert über alle zulässigen Routen und kann deshalb nur tiefer oder gleich liegen. Die **Lücke** ist (elementare Schranke − Schranke mit Kreisen) geteilt durch die elementare Schranke.
5. **Warum Kreise in der ersten Runde attraktiv sind:** Mit den Dualpreisen der Einzelfahrten (Preis = Hin- und Rückweg zum Kunden) hat die Route 0-i-j-i-0 genau doppelt so niedrige reduzierte Kosten wie 0-i-j-0, wenn Last und Fenster beide Besuche von i erlauben (Rechnung im Expander „📐 Mathematische Formulierung“).
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

# --- Seitenleiste ------------------------------------------------------------------------------------------------------------------------

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Szenario ist hervorgehoben
    st.header("🧮 Handbeispiel")
    st.caption("Für die Experimente 1 und 2 (sieben Kunden, zum Nachrechnen mit dem Stift).")
    h_regel = st.radio("Wege im Labeling (Experiment 1)", choices("h_regel"), key="h_regel",
                       help="„Kreise erlaubt“: nur Kunde i direkt nach i ist verboten. „elementar“: jeder Kunde höchstens einmal. Experiment 1 zeigt beides nebeneinander; die Wahl bestimmt, welches Protokoll und welcher Fahrplan unten stehen.")
    h_dual7 = st.slider("Dualpreis von Kunde 7 (Experiment 1)", *bounds("h_dual7"), key="h_dual7",
                        help="Preis, den der Master für den Besuch von Kunde 7 vorgibt. Voreinstellung 10 (Hin- und Rückweg zum Depot); die anderen Dualpreise sind fest.")
    h_runde = st.slider("Runde ansehen (Experiment 2)", *bounds("h_runde"), key="h_runde",
                        help="Welche Runde der Spaltenerzeugung mit Kreisen im Handbeispiel im Detail gezeigt wird: Dualpreise der Runde und Fahrplan der neuen Spalte.")
    st.header("🔧 Live-Rechnung")
    st.caption("Für die Experimente 3 und 4: die ganze Spaltenerzeugung auf einer zufälligen Instanz.")
    l_n = st.slider("Kunden n", *bounds("l_n"), key="l_n", help="Zahl der Kunden der zufälligen Instanz (Quadrat 100 × 100, Depot in der Mitte).")
    l_breite = st.select_slider("Breite der Zeitfenster", options=choices("l_breite"), key="l_breite",
                                help="Je breiter die Fenster, desto mehr Wege sind zulässig, desto häufiger passt ein zweiter Besuch am selben Kunden in den Zeitplan.")
    l_seed = st.number_input("Zufalls-Seed der Instanz", *bounds("l_seed"), key="l_seed", step=1)
    st.button("🎲 Neue Instanz generieren", width="stretch", on_click=randomize_seed)

sync_query_params({k_: st.session_state[k_] for k_ in ("h_regel", "h_dual7", "h_runde", "l_n", "l_breite", "l_seed")})

# ======================================================================================================================================
# Experiment 1: der Kreis im Labeling
# ======================================================================================================================================

st.subheader("🔬 Experiment 1: Der Kreis im Labeling – Schritt für Schritt am Handbeispiel")
st.markdown(
    f"""
Ein Depot und sieben Kunden auf einem Gitter, Entfernung = Manhattan-Abstand = Fahrzeit, Bedienzeit 2, Kapazität 6, späteste Rückkehr 38. Die Dualpreise sind die der ersten Runde (Hin- und Rückweg vom Depot);
nur der von **Kunde 7** ist mit dem Regler einstellbar. Gesucht ist die Route mit den kleinsten reduzierten Kosten, einmal mit erlaubten Kreisen, einmal elementar.
"""
)
hand_inst = S.handbeispiel()
hand_dual = S.hand_dualpreise(h_dual7)
st.dataframe(
    [{"Kunde": i, "Lage": f"({hand_inst.punkte[i][0]}, {hand_inst.punkte[i][1]})", "Entfernung zum Depot": hand_inst.dist[0][i], "Last": hand_inst.last[i],
      "Zeitfenster": f"[{hand_inst.frueh[i]}, {hand_inst.spaet[i]}]", "Dualpreis": hand_dual[i]} for i in range(1, 8)],
    hide_index=True, width="stretch",
)
st.caption("Depot bei (0, 0). Kunde 7 hat Dualpreis 10, wenn der Regler auf der Voreinstellung steht; ein Besuch kostet Last, Bedienzeit und Fahrzeit, und er bringt den Dualpreis des Kunden ein.")

kreis = _hand_kreis(h_dual7)
z1, ze = kreis["k1"], kreis["elem"]
for name, z in (("mit erlaubten Kreisen", z1), ("elementar", ze)):
    if z["fehler"]:
        st.error(f"Gegenprobe fehlgeschlagen ({name}): {z['fehler']}")
sel = z1 if h_regel == C.HAND_REGELN[0] else ze
m1, m2, m3, m4 = st.columns(4)
# Delta immer als „mein Wert minus Referenz“ (Referenz: elementar); die Farbe regelt delta_color (Vorzeichen-Falle, DEMO-PLAYBOOK §2).
m1.metric("Erzeugte Labels, Kreise erlaubt", E.fmt_int(z1["erzeugt"]), delta=f"{z1['erzeugt'] - ze['erzeugt']:+d} gegen elementar", delta_color="inverse")
m2.metric("Erzeugte Labels, elementar", E.fmt_int(ze["erzeugt"]), delta="Referenz", delta_color="off")
m3.metric("Bester Wert, Kreise erlaubt", E.fmt_wert(z1["bester_wert"]), delta=f"{z1['bester_wert'] - ze['bester_wert']:+d} gegen elementar", delta_color="inverse")
m4.metric("Bester Wert, elementar", E.fmt_wert(ze["bester_wert"]), delta="Referenz", delta_color="off")
st.caption(
    f"„Bester Wert“ sind die kleinsten reduzierten Kosten einer Route (kleiner ist besser). Gegenprobe durch Aufzählung aller zulässigen Routen (ohne Dominanz): mit erlaubten Kreisen {E.fmt_int(z1['aufz_wege'])} Routen, "
    f"davon {E.fmt_int(z1['aufz_kreis'])} mit Kreis und {E.fmt_int(z1['aufz_negativ'])} mit negativen reduzierten Kosten, bester Wert {E.fmt_wert(z1['aufz_wert'])}; "
    f"elementar {E.fmt_int(ze['aufz_wege'])} Routen, davon {E.fmt_int(ze['aufz_negativ'])} mit negativen reduzierten Kosten, bester Wert {E.fmt_wert(ze['aufz_wert'])}."
)

c1, c2 = st.columns([2, 3])
with c1:
    st.plotly_chart(V.build_labels_hand(z1, ze), width="stretch", key="hand_labels")
with c2:
    st.markdown(f"**Bester Weg: {h_regel}**")
    if sel["weg"]:
        st.markdown(f"Route {E.weg_text(sel['weg'])}" + (f" ({E.doppelt_text(sel['weg'])})" if A.hat_kreis(sel["weg"]) else " (ohne Kreis)") + ". " + E.aufstellung_text(hand_inst, hand_dual, sel["weg"]) + ".")
        st.dataframe(_fahrplan_tabelle(hand_inst, hand_dual, sel["weg"]), hide_index=True, width="stretch")
    else:
        st.info("Bei diesen Dualpreisen gibt es keine Route mit negativen reduzierten Kosten.")

tabelle = _hand_protokoll(h_regel, h_dual7)
lebend = E.ueberlebende_tabelle(tabelle)
st.markdown(f"**Label-Liste je Kunde: die {len(lebend)} Labels, die bei „{h_regel}“ am Ende übrig sind** (von {len(tabelle)} erzeugten)")
st.dataframe([{"Kunde": z["kunde"], "Teilweg": E.weg_text(z["weg"]), "Zeit": z["zeit"], "Kosten": E.fmt_wert(z["kosten"]), "Last": z["last"]} for z in lebend], hide_index=True, width="stretch")
with st.expander(f"📋 Protokoll: jedes der {len(tabelle)} erzeugten Labels ({h_regel})"):
    st.caption("Nummern in der Reihenfolge der Erzeugung (L0 ist das Startlabel am Depot). „Kosten“ sind reduzierte Kosten bis zum Kunden (Weglänge minus Dualpreise der besuchten Kunden).")
    st.dataframe([{"Label": f"L{z['id']}", "Teilweg": E.weg_text(z["weg"]) if z["weg"] else "(Depot)", "Kunde": z["kunde"], "Zeit": z["zeit"], "Kosten": E.fmt_wert(z["kosten"]), "Last": z["last"],
                   "Entscheidung": E.entscheidung_text(z)} for z in tabelle], hide_index=True, width="stretch")

kind, text = E.verdict_kreis_hand(z1, ze, kreis["kunde7"], h_dual7)
getattr(st, kind)(text)
st.markdown("---")

# ======================================================================================================================================
# Experiment 2: Spaltenerzeugung ohne Elementarität
# ======================================================================================================================================

st.subheader("🔬 Experiment 2: Spaltenerzeugung mit Kreisen – Runde für Runde am Handbeispiel")
st.markdown(
    """
Dasselbe Netz, jetzt die ganze Schleife aus Master und Pricing: Start mit den sieben Einzelfahrten, je Runde kommt die beste neue Spalte dazu, bis keine Route mehr negative reduzierte Kosten hat. Der Master ist exakt mit Brüchen gerechnet.
Links die Rechnung mit erlaubten Kreisen, rechts die elementare; der Wert des Masters ist in jeder Runde eine untere Schranke.
"""
)
cg1, cge = _hand_colgen(False), _hand_colgen(True)
gp1, gpe = _hand_gegenprobe(False), _hand_gegenprobe(True)


def _runden_tabelle(cg):
    zeilen = []
    for r in cg["lauf"]["runden"]:
        if r["neue"]:
            rc, route = r["neue"][0]
            neu, rck, kr = E.weg_text(route), E.fmt_wert(rc), E.doppelt_text(route) or "–"
        else:
            neu, rck, kr = "keine (Schranke erreicht)", "–", "–"
        zeilen.append({"Runde": r["nr"], "Wert des Masters": E.fmt_wert(r["wert"]), "neue Spalte": neu, "reduzierte Kosten": rck, "Kreis": kr, "erzeugte Labels": r["erzeugt"]})
    return zeilen


m1, m2, m3, m4 = st.columns(4)
lk = E.luecke(cge["schranke"], cg1["schranke"])
m1.metric("Schranke, Kreise erlaubt", E.fmt_wert(cg1["schranke"]), delta=f"{cg1['runden']} Runden, {E.fmt_int(cg1['labels'])} Labels", delta_color="off")
m2.metric("Schranke, elementar", E.fmt_wert(cge["schranke"]), delta=f"{cge['runden']} Runden, {E.fmt_int(cge['labels'])} Labels", delta_color="off")
m3.metric("Lücke", E.fmt_pct(lk, 2), delta="(elementar − Kreise erlaubt) / elementar", delta_color="off")
m4.metric("Neue Spalten mit Kreis", f"{cg1['mit_kreis']} von {len(cg1['neue'])}", delta=f"elementar: {cge['mit_kreis']} von {len(cge['neue'])}", delta_color="off")
t1, t2 = st.columns(2)
with t1:
    st.markdown("**Kreise erlaubt**")
    st.dataframe(_runden_tabelle(cg1), hide_index=True, width="stretch")
with t2:
    st.markdown("**Elementar**")
    st.dataframe(_runden_tabelle(cge), hide_index=True, width="stretch")
st.plotly_chart(V.build_master_verlauf([r["wert"] for r in cg1["lauf"]["runden"]], [r["wert"] for r in cge["lauf"]["runden"]]), width="stretch", key="hand_master")

runde = min(h_runde, cg1["runden"])
r_info = cg1["lauf"]["runden"][runde - 1]
st.markdown(f"**Runde {runde} mit erlaubten Kreisen im Detail** (Regler „Runde ansehen“ in der Seitenleiste)")
d1, d2 = st.columns([2, 3])
with d1:
    st.dataframe([{"Kunde": j, "Dualpreis der Runde": E.fmt_wert(r_info["dual"][j])} for j in range(1, 8)], hide_index=True, width="stretch")
with d2:
    if r_info["neue"]:
        rc, route = r_info["neue"][0]
        st.markdown(f"Neue Spalte: Route {E.weg_text(route)} ({E.doppelt_text(route) or 'ohne Kreis'}), reduzierte Kosten {E.fmt_wert(rc)}. " + E.aufstellung_text(hand_inst, r_info["dual"], route) + ".")
        st.dataframe(_fahrplan_tabelle(hand_inst, r_info["dual"], route), hide_index=True, width="stretch")
    else:
        st.info(f"In Runde {runde} findet das Pricing keine Route mit negativen reduzierten Kosten: der Wert des Masters ({E.fmt_wert(r_info['wert'])}) ist die Schranke.")

st.markdown("**Endlösung des Masters mit erlaubten Kreisen** (Spalten mit positiver Menge)")
st.dataframe([{"Route": E.weg_text(r), "Menge": E.fmt_wert(x), "Kosten der Route": A.weg_laenge(hand_inst, r), "Kosten mal Menge": E.fmt_wert(x * A.weg_laenge(hand_inst, r)), "Kreis": E.doppelt_text(r) or "–"} for r, x in cg1["ende"]],
             hide_index=True, width="stretch")
halbe = E.hand_halbe_kreisfahrt(cg1, hand_inst)
if halbe:
    st.caption(
        f"Die Spalte {E.weg_text(halbe['route'])} zählt die Kunden {', '.join(str(j) for j in halbe['doppelt'])} im Master je zweimal; mit der Menge {E.fmt_wert(halbe['menge'])} überdeckt sie jeden von ihnen einmal und kostet {E.fmt_wert(halbe['anteilig'])} "
        f"(die ganze Route kostet {halbe['kosten']}). Eine elementare Fahrt {E.weg_text(halbe['elementar_route'])} überdeckt dieselben Kunden je einmal und kostet {halbe['elementar_kosten']}: so kommt die tiefere Schranke zustande."
    )
kind, text = E.verdict_colgen_hand(cg1, cge, gp1, gpe)
getattr(st, kind)(text)
st.caption(f"Das Handbeispiel ist ein kleines Netz mit sieben Kunden und enger Kapazität: seine Lücke ({E.fmt_pct(lk, 2)}) ist größer als jedes Mittel der Messreihen zur elementaren Schranke in Experiment 5 (höchstens {E.fmt_pct(max(z['mittel'] for z in B.luecke_elementar_tabelle()), 2)}). Wie groß sie bei Zufallsinstanzen ist, zeigen die Experimente 3 und 5.")
st.markdown("---")

# ======================================================================================================================================
# Experiment 3: Größe und Breite (live)
# ======================================================================================================================================

st.subheader("🔬 Experiment 3: Größe und Breite – die ganze Spaltenerzeugung auf einer Zufallsinstanz, live")
st.markdown(
    f"""
Eine zufällige Instanz mit **{l_n} Kunden** (Zufalls-Seed {l_seed}), Zeitfenster der Breite {l_breite}. Die Spaltenerzeugung läuft zweimal: mit erlaubten Kreisen und elementar (Überdeckungs-Master, je Runde bis zu {C.MAX_NEUE_SPALTEN} neue Spalten).
Die elementare Rechnung bricht bei sehr großen Einstellungen an einer festen Obergrenze ab ({E.fmt_int(C.LIVE_MAX_VERGLEICHE_ELEMENTAR)} Dominanztests); die Obergrenze zählt Dominanztests, keine Sekunden. Jede neue Spalte wird vor der Anzeige unabhängig geprüft.
"""
)
with st.spinner("Spaltenerzeugung wird gerechnet (die größten Einstellungen brauchen einige Sekunden) …"):
    live = _live(int(l_n), int(l_breite), int(l_seed))
if live["fehler"]:
    st.error("Prüfung fehlgeschlagen: " + live["fehler"])
k1, el = live["k1"], live["elem"]
m1, m2, m3, m4 = st.columns(4)
m1.metric("Schranke, Kreise erlaubt", E.fmt_dec(k1["schranke"], 2), delta=f"{k1['runden']} Runden", delta_color="off")
m2.metric("Schranke, elementar", "nicht erreicht" if el["abgebrochen"] else E.fmt_dec(el["schranke"], 2), delta="abgebrochen" if el["abgebrochen"] else f"{el['runden']} Runden", delta_color="off")
m3.metric("Lücke", "–" if live["luecke"] is None else E.fmt_pct(live["luecke"], 2), delta="(elementar − Kreise erlaubt) / elementar", delta_color="off")
m4.metric("Neue Spalten mit Kreis", f"{k1['mit_kreis']} von {k1['spalten']}", delta=E.fmt_pct(k1["mit_kreis"] / k1["spalten"]) if k1["spalten"] else "–", delta_color="off")
c1, c2 = st.columns([2, 3])
with c1:
    st.plotly_chart(V.build_live_labels(live), width="stretch", key="live_labels")
with c2:
    st.dataframe([
        {"Rechnung": "Kreise erlaubt (k = 1)", "Schranke": k1["schranke"], "Runden": k1["runden"], "erzeugte Labels": k1["labels"], "Dominanztests": k1["vergleiche"]},
        {"Rechnung": "elementar" + (" (abgebrochen)" if el["abgebrochen"] else ""), "Schranke": None if el["abgebrochen"] else el["schranke"], "Runden": el["runden"], "erzeugte Labels": el["labels"], "Dominanztests": el["vergleiche"]},
    ], hide_index=True, width="stretch", column_config={"Schranke": st.column_config.NumberColumn(format="%.2f"), "erzeugte Labels": GANZ, "Dominanztests": GANZ})
    st.caption(f"Spalten der Endlösung (Menge über der Rauschgrenze): {k1['ende_spalten']}, davon mit Kreis {k1['ende_kreis']}.")
st.caption(
    f"Rechenzeit dieses Laufs zusammen: {E.fmt_dec(live['sekunden'])} s (nur zur Information; sie hängt vom Rechner ab, die Zahl der Labels nicht). "
    "Zahlen der Spalten und Runden können sich auf einem anderen Rechner leicht unterscheiden (der Master-Löser kann bei gleich guten Lösungen andere Dualpreise liefern), die Schranken nicht."
)
kind, text = E.verdict_live(live)
getattr(st, kind)(text)
st.caption("Eine Instanz ist ein Einzelfall. Wie die Lücke über mehrere Instanzen streut, zeigt Experiment 5.")
st.markdown("---")

# ======================================================================================================================================
# Experiment 4: Welcher Kreis?
# ======================================================================================================================================

st.subheader("🔬 Experiment 4: Welcher Kreis? Länge und Wiederholungen")
st.markdown(
    """
Der **kürzeste Kreis** einer Spalte zählt die Kanten zwischen zwei Besuchen desselben Kunden: zwei Kanten heißen „Hin und zurück“ (i, j, i), drei Kanten (i, j, l, i). Die **Wiederholungen** einer Spalte sind ihre Länge minus die Zahl der verschiedenen Kunden.
Links die Spalten der gewählten Instanz aus Experiment 3, daneben die feste Messreihe (n = 30, Zufalls-Seeds 0 bis 5), deren Breite Sie hier wählen.
"""
)
k_breite = st.radio("Breite der festen Messreihe zum Vergleich", B.kreise_breiten(), key="k_breite", horizontal=True, index=B.kreise_breiten().index(100))
fest = B.kreise_summe(k_breite)
live_kz = {"mit_kreis": k1["mit_kreis"], "kuerzeste": k1["kuerzeste"], "wiederholungen": k1["wiederholungen"]}
c1, c2 = st.columns(2)
with c1:
    st.plotly_chart(V.build_kreislaengen(live_kz, fest), width="stretch", key="kreislaengen")
with c2:
    st.plotly_chart(V.build_wiederholungen(live_kz, fest), width="stretch", key="wiederholungen")
st.dataframe([
    {"Quelle": f"diese Instanz (n = {l_n}, Breite {l_breite})", "Kreis-Spalten": k1["mit_kreis"], "kürzester Kreis: 2 Kanten": k1["kuerzeste"]["2"], "3 Kanten": k1["kuerzeste"]["3"], "4 und mehr": k1["kuerzeste"]["4+"]},
    {"Quelle": f"feste Messreihe (n = 30, Breite {k_breite})", "Kreis-Spalten": fest["mit_kreis"], "kürzester Kreis: 2 Kanten": fest["kuerzeste"]["2"], "3 Kanten": fest["kuerzeste"]["3"], "4 und mehr": fest["kuerzeste"]["4+"]},
], hide_index=True, width="stretch", column_config={"Kreis-Spalten": GANZ, "kürzester Kreis: 2 Kanten": GANZ, "3 Kanten": GANZ, "4 und mehr": GANZ})
kind, text = E.verdict_kreislaengen(live_kz, fest, k_breite)
getattr(st, kind)(text)
st.caption("Wie oft die Kreise Hin-und-zurück-Kreise sind, gilt für die gemessenen Breiten und zufällig verteilte Instanzen; ob ein größeres Gedächtnis sie verhindern würde, wird hier nicht gemessen.")
st.markdown("---")

# ======================================================================================================================================
# Experiment 5: Bänder
# ======================================================================================================================================

st.subheader("🔬 Experiment 5: Messreihen mit mehreren Instanzen (Bänder)")
st.markdown(
    """
Feste Messreihen, mit dem Kern dieser Demo gerechnet (Ausnahme: die Zeilen mit Bezug k = 16, siehe unten). Zufällig verteilte Instanzen, Zufalls-Seeds ab 0, Überdeckungs-Master.
**(a)** Der Anteil der Spalten mit Kreis hängt an der Fensterbreite. **(b)** Die Lücke der Schranke zur elementaren (oder zu einer anderen Bezugsrechnung) in Prozent der Bezugsschranke; Mittel und Maximum über die Instanzen mit fertiger Bezugsrechnung.
"""
)
st.markdown("**(a) Anteil der Spalten mit Kreis** (n = 30, Kreise erlaubt, Instanzen je Breite: " + str(B.kreise_summe(B.kreise_breiten()[0])["instanzen"]) + ")")
kt = B.kreise_tabelle()
c1, c2 = st.columns([3, 2])
with c1:
    st.dataframe(
        [{"Breite": z["breite"], "neue Spalten": z["neue_spalten"], "davon mit Kreis": z["mit_kreis"], "Anteil": _prozent(z["anteil_neue"]), "Spalten der Endlösung": z["ende_spalten"],
          "davon mit Kreis": z["ende_kreis"], "Anteil der Endlösung": _prozent(z["anteil_ende"]), "Anteil an der Menge": _prozent(z["anteil_menge"]), "kürzester Kreis 2 Kanten": z["kuerzeste"]["2"]} for z in kt],
        hide_index=True, width="stretch", column_config={"Anteil": PROZENT, "Anteil der Endlösung": PROZENT, "Anteil an der Menge": PROZENT, "neue Spalten": GANZ, "davon mit Kreis": GANZ, "Spalten der Endlösung": GANZ},
    )
with c2:
    st.plotly_chart(V.build_kreisanteil(kt), width="stretch", key="band_kreise")
kind, text = E.verdict_kreise_baender(kt)
getattr(st, kind)(text)

st.markdown("**(b) Lücke der Schranke bei erlaubten Kreisen**")
b_bezug = st.radio("Bezugsrechnung", list(B.BEZUEGE), key="b_bezug", horizontal=True, format_func=lambda x: B.BEZUEGE[x])
if b_bezug == "elementar":
    zeilen = B.luecke_elementar_tabelle()
elif b_bezug == "k = 8":
    zeilen = B.luecke_k8_tabelle()
else:
    zeilen = B.luecke_k16_tabelle()
st.dataframe(
    [{"Typ": B.TYPEN.get(z["typ"], z["typ"]), "n": z["n"], "Breite": z["breite"], "Instanzen (Zahl)": z.get("instanzen"), "fertig": z.get("fertig", z.get("instanzen")),
      "Lücke, Mittel": _prozent(z["mittel"]), "Lücke, Maximum": _prozent(z["maximum"]), "Lücke null in": z["null_in"], "Labels, Median, Kreise erlaubt": z["labels_k1"], "Labels, Median, Bezug": z["labels_ref"]} for z in zeilen],
    hide_index=True, width="stretch",
    column_config={"Lücke, Mittel": PROZENT3 if b_bezug == "k = 16" else PROZENT2, "Lücke, Maximum": PROZENT3 if b_bezug == "k = 16" else PROZENT2, "Labels, Median, Kreise erlaubt": GANZ, "Labels, Median, Bezug": GANZ},
)
if b_bezug == "elementar":
    st.plotly_chart(V.build_luecke(zeilen), width="stretch", key="band_luecke")
    kind, text = E.verdict_luecke_baender(zeilen)
    getattr(st, kind)(text)
    n30 = B.luecke_n30_vergleich()
    if n30:
        st.warning(
            f"Breite 100, n = 30: In der Messung vor dem Bau brachen {n30['abgebrochen_vor']} von {n30['instanzen']} elementaren Läufen an einer Zeitgrenze ab; die {n30['fertig_vor']} fertigen hatten eine mittlere Lücke von {E.fmt_dec(100 * n30['mittel_vor'], 2)}{E.NBSP}%. "
            f"Mit der Obergrenze in Dominanztests ({E.fmt_int(B.grenze_vergleiche())}) sind hier alle {n30['fertig_hier']} Läufe fertig, die mittlere Lücke ist {E.fmt_dec(100 * n30['mittel_hier'], 2)}{E.NBSP}%: die zuerst fertigen Instanzen hatten die größeren Lücken."
        )
    st.caption("Die Ergebnisse dieser Zeilen sind mit dem Kern dieser Demo neu gerechnet und stimmen in jeder Schranke mit der Messung vor dem Bau überein, soweit diese fertig wurde "
               f"({B.vormessung_vergleiche()['verglichen']} Schranken verglichen, {B.vormessung_vergleiche()['abweichend']} Abweichungen).")
elif b_bezug == "k = 8":
    st.info("Bezug k = 8 (n = 30, je 5 Instanzen; zufällig und gruppiert Breite 100, „lang“ mit Horizont 500, Kapazität 120 und Breite 60): hier wird gegen die Schranke bei k = 8 gemessen, weil die elementare Rechnung bei n = 30 oft zu lange dauert. "
            "Die Lücke zur elementaren Schranke ist mindestens so groß. Neu gerechnet mit dem Kern dieser Demo.")
else:
    st.warning("Bezug k = 16 (n = 50 und 100, je 12 Instanzen): **nicht neu gerechnet**, die Zahlen stammen nur aus der Auswertungsdatei der Messung vor dem Bau (zu rechenaufwendig für diese Demo). "
               "Bei Breite 20 und n = 100 ist die Lücke in 12 von 12 Instanzen null.")
st.caption("Aussagen gelten nur für die gemessenen Größen und Breiten, 5 bis 12 Instanzen je Zeile, kein Konfidenzmaß. "
           "Gruppierte und lange Instanzen sind nur gegen k = 8 (und gruppierte gegen k = 16) gemessen.")
st.markdown("---")

# ======================================================================================================================================
# Grenzen, Annahmen, Mathematik
# ======================================================================================================================================

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(T.annahmen_tabelle())

with st.expander("⚠️ Annahmen, Grenzen und bekannte Probleme"):
    st.markdown(T.assumptions_markdown())

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(T.MATH_LESEHILFE)
    st.markdown(T.MATH_FORMELN)

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zur Reihe: [Ressourcenwege: von der Grenze zur Verfahrenswahl](https://sebastianhanisch.net/konzepte-ressourcenwege.html)."
)
