"""Erzeugt die festen Messreihen data/baender_kreise.json und data/baender_luecke.json mit dem Kern dieser Demo (nicht aus fremden Rohdateien).

Aufruf (im Demo-Ordner, mit dem Python des Test-venv):  python tools/baender_erzeugen.py [--prozesse 3] [--vormessung PFAD]

Rechnet neu:
* Anteil der Spalten mit Kreis: n = 30, Breite 40, 100 und 200, Zufalls-Seeds 0 bis 5, Gedächtnis k = 1, Überdeckungs-Master (HiGHS);
* Lücke der Schranke bei k = 1 zur elementaren Schranke: n = 10, 15, 20, 25, 30, Breite 40 und 100, Seeds 0 bis 5;
* Lücke der Schranke bei k = 1 zur Schranke bei k = 8: n = 30, drei Instanztypen (zufällig, gruppiert, lang), Seeds 0 bis 4.
Nicht neu gerechnet (zu teuer, Zahlen nur aus der Auswertungsdatei der Vormessung übernommen): Lücke zu k = 16 bei n = 50 und n = 100 (V8).

Ist der Ordner der Vormessung erreichbar, vergleicht das Werkzeug jede neu gerechnete Schranke mit der dort gemessenen (Toleranz 1e-3, die Dateien nennen vier Stellen)
und schreibt Zahl der Vergleiche und der Abweichungen in die JSON-Dateien; die Summen der Spalten mit Kreis werden mit den Logdateien der Vormessung verglichen.
Elementare Läufe haben eine Obergrenze in Dominanztests (`GRENZE_VERGLEICHE`, eine Zählung, keine Zeitgrenze); wird sie erreicht, gilt der Lauf als abgebrochen."""

import argparse
import json
import re
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import kip_algorithm as A  # noqa: E402
import kip_master as M  # noqa: E402
import kip_scenario as S  # noqa: E402
from kip_constants import MENGE_EPS  # noqa: E402

DATA = ROOT / "data"
GRENZE_VERGLEICHE = 600_000_000          # elementare Läufe: Abbruch nach so vielen Dominanztests (alle Pricing-Aufrufe zusammen)
SEEDS = tuple(range(6))
SEEDS_V7 = tuple(range(5))
TYPEN_V7 = {"zufall": dict(), "cluster": dict(gruppiert=True), "lang": dict(horizont=500.0, kapazitaet=120)}
BREITE_V7 = {"zufall": 100, "cluster": 100, "lang": 60}
N_LUECKE = (10, 15, 20, 25, 30)
BREITEN_LUECKE = (40, 100)
BREITEN_KREISE = (40, 100, 200)


# ---------------------------------------------------------------------------------------------------------------------------------
# Einzelne Rechnungen (laufen in Kindprozessen)
# ---------------------------------------------------------------------------------------------------------------------------------

def zeile_kreise(args) -> dict:
    breite, seed = args
    inst = S.make_instance(30, seed, breite)
    lauf = M.spaltenerzeugung(inst, 1)
    neue = M.neue_spalten(lauf, inst.n)
    kreis = [r for r in neue if A.hat_kreis(r)]
    kuerzeste = {"2": 0, "3": 0, "4+": 0}
    wdh = {}
    for r in kreis:
        k = A.kuerzester_kreis(r)
        kuerzeste["2" if k == 2 else "3" if k == 3 else "4+"] += 1
        wdh[str(A.wiederholungen(r))] = wdh.get(str(A.wiederholungen(r)), 0) + 1
    ende = M.endloesung(lauf, MENGE_EPS)
    return {"breite": breite, "seed": seed, "runden": len(lauf["runden"]), "neue_spalten": len(neue), "mit_kreis": len(kreis), "schranke": lauf["schranke"],
            "ende_spalten": len(ende), "ende_kreis": sum(1 for r, _x in ende if A.hat_kreis(r)),
            "ende_menge": sum(x for _r, x in ende), "ende_menge_kreis": sum(x for r, x in ende if A.hat_kreis(r)),
            "kuerzester_kreis": kuerzeste, "wiederholungen": wdh,
            "laenge_neue": sum(len(r) for r in neue), "laenge_kreis": sum(len(r) for r in kreis), "labels": lauf["labels"]}


def zeile_luecke_elementar(args) -> dict:
    n, breite, seed = args
    inst = S.make_instance(n, seed, breite)
    k1 = M.spaltenerzeugung(inst, 1)
    el = M.spaltenerzeugung(inst, n, max_vergleiche=GRENZE_VERGLEICHE)
    return {"n": n, "breite": breite, "seed": seed, "schranke_k1": k1["schranke"], "schranke_ref": el["schranke"], "labels_k1": k1["labels"], "labels_ref": el["labels"],
            "abgebrochen": el["abgebrochen"]}


def zeile_luecke_k8(args) -> dict:
    typ, seed = args
    inst = S.make_instance(30, seed, BREITE_V7[typ], **TYPEN_V7[typ])
    k1 = M.spaltenerzeugung(inst, 1)
    k8 = M.spaltenerzeugung(inst, 8)
    return {"typ": typ, "seed": seed, "schranke_k1": k1["schranke"], "schranke_ref": k8["schranke"], "labels_k1": k1["labels"], "labels_ref": k8["labels"], "abgebrochen": False}


# ---------------------------------------------------------------------------------------------------------------------------------
# Vergleich mit den Dateien der Vormessung (nur wenn erreichbar)
# ---------------------------------------------------------------------------------------------------------------------------------

def lies_schranken(pfad: Path, spalten: dict) -> dict:
    """Liest eine Messdatei der Vormessung mit Kopfzeile; `spalten` benennt die Spaltenindizes: {"schluessel": [Indizes], "schranke": Index}. Rückgabe {Schlüssel: Schranke oder None}."""
    out = {}
    for zeile in pfad.read_text(encoding="utf-8").splitlines()[1:]:
        p = zeile.split()
        if len(p) <= spalten["schranke"]:
            continue
        schluessel = tuple(p[i] for i in spalten["schluessel"])
        out[schluessel] = None if p[spalten["schranke"]] == "NA" else float(p[spalten["schranke"]])
    return out


def vergleiche_schranken(neu: dict, alt: dict, toleranz: float = 1e-3) -> dict:
    """Vergleicht neu gerechnete Schranken (None = abgebrochen) mit der Vormessung. Rückgabe: verglichen (beide fertig), abweichend, nur_neu_fertig (Zahl und Zufalls-Seeds der Instanzen, die nur hier fertig wurden), nur_vormessung_fertig."""
    verglichen = abweichend = nur_alt = 0
    nur_neu = []
    for schluessel, wert in neu.items():
        if schluessel not in alt:
            continue
        a = alt[schluessel]
        if wert is not None and a is not None:
            verglichen += 1
            abweichend += abs(wert - a) > toleranz
        elif wert is not None:
            nur_neu.append(int(schluessel[2]) if len(schluessel) > 3 else int(schluessel[0]))
        elif a is not None:
            nur_alt += 1
    return {"verglichen": verglichen, "abweichend": abweichend, "nur_neu_fertig": len(nur_neu), "nur_neu_fertig_seeds": sorted(nur_neu), "nur_vormessung_fertig": nur_alt}


def lies_summen_log(pfad: Path):
    """Liest aus einem Log von p06_kreise.py die Zeile „gesamt: X von Y neuen Spalten mit Kreis“; Rückgabe (X, Y)."""
    m = re.search(r"gesamt: (\d+) von (\d+) neuen Spalten mit Kreis", pfad.read_text(encoding="utf-8"))
    return (int(m.group(1)), int(m.group(2))) if m else None


def lies_v8(pfad: Path) -> list:
    """Liest die Tabellen von V8 (Lücke zu k = 16): je Zelle (Typ, n, Breite) Instanzen, Lücke mittel und max in Prozent bei k = 1, Zahl der Instanzen mit Lücke 0, Median der Labels bei k = 1 und k = 16."""
    zellen = []
    text = pfad.read_text(encoding="utf-8")
    for block in re.split(r"\n(?=### )", text):
        kopf = re.match(r"### (\w+), n = (\d+), Breite (\d+)\s+\((\d+) Instanzen\)", block)
        if not kopf:
            continue
        zeilen = {}
        for z in block.splitlines():
            if z.startswith("| ") and not z.startswith("| k ") and not z.startswith("|---"):
                zeilen[z.split("|")[1].strip()] = [c.strip() for c in z.split("|")[2:-1]]
        r1, r16 = zeilen["1"], zeilen["16"]
        zellen.append({"typ": kopf.group(1), "n": int(kopf.group(2)), "breite": int(kopf.group(3)), "instanzen": int(kopf.group(4)),
                       "luecke_mittel": float(r1[5]), "luecke_max": float(r1[6]), "luecke_null_in": int(r1[7].split("/")[0]),
                       "labels_median_k1": int(r1[2]), "labels_median_k16": int(r16[2])})
    return zellen


# ---------------------------------------------------------------------------------------------------------------------------------
# Hauptprogramm
# ---------------------------------------------------------------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prozesse", type=int, default=3)
    ap.add_argument("--vormessung", default=str(ROOT.parent / "label-setting-planung" / "vormessung"))
    ap.add_argument("--nur", choices=("kreise", "luecke"), default=None)
    args = ap.parse_args()
    vor = Path(args.vormessung)
    hat_vor = vor.is_dir()
    print("Vormessung erreichbar:", hat_vor, flush=True)
    DATA.mkdir(exist_ok=True)

    with ProcessPoolExecutor(max_workers=args.prozesse) as pool:
        if args.nur in (None, "kreise"):
            zeilen = list(pool.map(zeile_kreise, [(b, s) for b in BREITEN_KREISE for s in SEEDS]))
            zellen = []
            logs = {40: "run_p06_b40.log", 100: "run_p06.log", 200: "run_p06_b200.log"}
            for b in BREITEN_KREISE:
                z = [r for r in zeilen if r["breite"] == b]
                zelle = {"n": 30, "breite": b, "typ": "zufall", "k": 1, "zeilen": z,
                         "quelle": "neu gerechnet mit tools/baender_erzeugen.py dieser Demo (Kern kip_algorithm.py, Master HiGHS)"}
                if hat_vor and (vor / logs[b]).exists():
                    alt = lies_summen_log(vor / logs[b])
                    neu = (sum(r["mit_kreis"] for r in z), sum(r["neue_spalten"] for r in z))
                    zelle["vormessung"] = {"datei": f"label-setting-planung/vormessung/{logs[b]}", "mit_kreis": alt[0], "neue_spalten": alt[1], "gleich": alt == neu}
                    print(f"Kreise Breite {b}: neu {neu}, Vormessung {alt}", flush=True)
                zellen.append(zelle)
            (DATA / "baender_kreise.json").write_text(json.dumps({"zellen": zellen}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

        if args.nur in (None, "luecke"):
            aufgaben = [(n, b, s) for n in reversed(N_LUECKE) for b in reversed(BREITEN_LUECKE) for s in SEEDS]
            zeilen = list(pool.map(zeile_luecke_elementar, aufgaben, chunksize=1))
            zellen = []
            alt_n30 = lies_schranken(vor / "out_v1_n30.txt", {"schluessel": [0, 1, 2, 3], "schranke": 4}) if hat_vor else {}
            for n in N_LUECKE:
                for b in BREITEN_LUECKE:
                    z = sorted((r for r in zeilen if r["n"] == n and r["breite"] == b), key=lambda r: r["seed"])
                    zelle = {"id": f"elementar_n{n}_b{b}", "bezug": "elementar", "n": n, "breite": b, "typ": "zufall", "neu_gerechnet": True, "zeilen": z,
                             "grenze_vergleiche": GRENZE_VERGLEICHE,
                             "quelle": "neu gerechnet mit tools/baender_erzeugen.py dieser Demo (Kern kip_algorithm.py, Master HiGHS)"}
                    if hat_vor:
                        datei = "out_v1_n30.txt" if n == 30 else f"run_p07_n{n}.log"
                        alt = alt_n30 if n == 30 else lies_schranken(vor / datei, {"schluessel": [0, 1, 2, 3], "schranke": 4})
                        neu_k1 = {(str(n), str(b), str(r["seed"]), "1"): r["schranke_k1"] for r in z}
                        neu_el = {(str(n), str(b), str(r["seed"]), str(n)): r["schranke_ref"] for r in z}
                        zelle["vormessung"] = {"datei": f"label-setting-planung/vormessung/{datei}", "k1": vergleiche_schranken(neu_k1, alt), "elementar": vergleiche_schranken(neu_el, alt)}
                        print(f"Lücke elementar n={n} Breite {b}: {zelle['vormessung']}", flush=True)
                    zellen.append(zelle)
            zeilen7 = list(pool.map(zeile_luecke_k8, [(t, s) for t in TYPEN_V7 for s in SEEDS_V7], chunksize=1))
            for typ in TYPEN_V7:
                z = sorted((r for r in zeilen7 if r["typ"] == typ), key=lambda r: r["seed"])
                zelle = {"id": f"k8_{typ}", "bezug": "k = 8", "n": 30, "breite": BREITE_V7[typ], "typ": typ, "neu_gerechnet": True, "zeilen": z,
                         "quelle": "neu gerechnet mit tools/baender_erzeugen.py dieser Demo (Kern kip_algorithm.py, Master HiGHS)"}
                if hat_vor:
                    datei = f"out_v7_{typ}.txt"
                    alt = {}
                    for zeile in (vor / datei).read_text(encoding="utf-8").splitlines()[1:]:
                        p = zeile.split()
                        if p[4] == "cover":
                            alt[(p[3], p[5])] = None if p[6] == "NA" else float(p[6])
                    neu = {}
                    for r in z:
                        neu[(str(r["seed"]), "1")] = r["schranke_k1"]
                        neu[(str(r["seed"]), "8")] = r["schranke_ref"]
                    zelle["vormessung"] = {"datei": f"label-setting-planung/vormessung/{datei}", "k1_und_k8": vergleiche_schranken(neu, alt)}
                    print(f"Lücke k = 8 {typ}: {zelle['vormessung']}", flush=True)
                zellen.append(zelle)
            if hat_vor:
                for z in lies_v8(vor / "out_v8_auswertung.txt"):
                    zellen.append({"id": f"k16_{z['typ']}_n{z['n']}_b{z['breite']}", "bezug": "k = 16", "neu_gerechnet": False, "zusammenfassung": z, "n": z["n"], "breite": z["breite"],
                                   "typ": z["typ"], "quelle": "label-setting-planung/vormessung/out_v8_auswertung.txt (nicht neu gerechnet)"})
            (DATA / "baender_luecke.json").write_text(json.dumps({"zellen": zellen}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("fertig", flush=True)


if __name__ == "__main__":
    main()
