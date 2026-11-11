# Kreise im Pricing: wie oft, und was kosten sie? – Streamlit-Demo

**[→ Demo live ausprobieren](https://sebastianhanisch-kreise-im-pricing-demo.streamlit.app/)**

Interaktive **Konzepte-Demo** der Reihe „Ressourcenwege und Spaltenerzeugung“ im Portfolio von [Sebastian Hanisch](https://sebastianhanisch.net) (Operations Research und Machine Learning).
Im **Pricing** der Spaltenerzeugung sucht das **Label-Setting** die Route mit den kleinsten **reduzierten Kosten** (Weglänge minus die **Dualpreise**, die der Master je Kunde vorgibt). Elementar, also mit jedem Kunden höchstens einmal, ist das aufwendig (jedes Label muss sich alle besuchten Kunden merken);
eine Möglichkeit ist deshalb, **Kreise** zuzulassen: ein Kunde darf mehrfach vorkommen, nur „Kunde i direkt nach Kunde i“ ist verboten. Diese Demo zeigt, **wie oft dann neue Spalten einen Kreis enthalten und wie viel tiefer die untere Schranke der Spaltenerzeugung liegt als die elementare**.

Die Grundlagen stehen in den Nachbardemos der Reihe: [weg-mit-grenzen-demo](https://github.com/sebastian-hanisch/weg-mit-grenzen-demo) (ein Weg mit Grenze), [dominanz-labels-demo](https://github.com/sebastian-hanisch/dominanz-labels-demo) (die Dominanzregel),
[zeitfenster-labeling-demo](https://github.com/sebastian-hanisch/zeitfenster-labeling-demo) (Zeitfenster und Warten), [mehrere-grenzen-demo](https://github.com/sebastian-hanisch/mehrere-grenzen-demo) (mehrere Grenzen) und
[pricing-dualpreise-demo](https://github.com/sebastian-hanisch/pricing-dualpreise-demo) (das Pricing aus Dualpreisen, der Master und die Schleife); hier sind sie vorausgesetzt. Die elementare Rechnung als Gegenpol stellt
[elementar-pricing-demo](https://github.com/sebastian-hanisch/elementar-pricing-demo) ins Zentrum (Was kostet es, Kreise ganz zu verbieten?); [ng-routen-demo](https://github.com/sebastian-hanisch/ng-routen-demo) fragt, wie viel Gedächtnis das Preisproblem braucht.
Als Anwendung dient [crew-pairing-demo](https://github.com/sebastian-hanisch/crew-pairing-demo): Dort läuft das Labeling über die nach Abfahrt geordneten Fahrten; ob dort Kreise überhaupt vorkommen können, ist hier nicht untersucht (aus der README gelesen, im Code nicht geprüft).
**Abgrenzung:** [hub-labeling-demo](https://github.com/sebastian-hanisch/hub-labeling-demo) (Kürzeste-Wege-Reihe) meint mit „Label“ etwas anderes, nämlich eine Liste von Hubs für Abstandsabfragen; hier ist ein Label ein Teilweg samt Kosten, Zeit und Last.

## Kernfrage

Wie oft enthalten neue Spalten einen Kreis, wenn das Pricing Kunden mehrfach besuchen darf, und wie viel tiefer liegt die Schranke? Die **Schranke** ist der Wert des Masters, wenn das Pricing keine Route mit negativen reduzierten Kosten mehr findet;
die **Lücke** ist (elementare Schranke − Schranke mit erlaubten Kreisen) geteilt durch die elementare Schranke. Gemessen werden außerdem **erzeugte Labels**; Sekunden stehen nur zur Information in der App.
Alle Messungen: eigene Solomon-artige Instanzen (nicht die Originalinstanzen), zufällig verteilt, soweit nicht anders genannt; Überdeckungs-Master; Python.

## Befunde und Korrekturen gegenüber dem Plan

- **n = 30, Breite 100: Die Lücke ist kleiner als zuerst gemessen.** In der Messung vor dem Bau brachen 3 von 6 elementaren Läufen an einer Zeitgrenze ab; die 3 fertigen hatten eine mittlere Lücke von 4,82 %. Mit einer Obergrenze in Dominanztests statt in Sekunden
  sind alle 6 Läufe fertig, die mittlere Lücke ist 3,33 % (Maximum unverändert 6,80 %): Die zuerst fertigen Instanzen hatten im Mittel die größeren Lücken (Tabellenzeile M).
- **Der Regler „Dualpreis von Kunde 7“ zeigt nicht „Kreis ja oder nein“.** Der beste Weg mit erlaubten Kreisen enthält bei jedem Dualpreis von 2 bis 14 einen Kreis, bei kleinem Dualpreis von Kunde 7 über Kunde 5. Das Urteil „lohnt sich“ gilt deshalb dem Kreis über Kunde 7:
  der beste Weg mit Kunde 7 mindestens zweimal ist ab Dualpreis 6 besser als der beste elementare Weg (Tabellenzeile C).
- **Der Master des Handbeispiels ist exakt (Brüche) im Kern der Demo**, nicht nur in den Tests: Nur so stehen die Runden und der Wert 83/3 genau da, ohne dass ein anderer Löser bei gleich guten Lösungen andere Dualpreise liefert. Die Zufallsinstanzen laufen mit HiGHS; beide Master sind gegeneinander getestet.
- **Die Obergrenzen zählen Dominanztests statt Sekunden** (Live-Rechnung 30 Millionen, Messreihen 600 Millionen), damit der Abbruch auf jedem Rechner derselbe ist.
- **Alle Bezugsschranken sind mit dem Kern dieser Demo neu gerechnet**, außer der Reihe „Lücke zu k = 16“ (n = 50 und 100, zu rechenaufwendig): Sie stammt nur aus der Auswertungsdatei der Messung vor dem Bau und steht in der App und hier mit diesem Vermerk.
  Jede neu gerechnete Schranke stimmt mit der Messung vor dem Bau überein, soweit diese fertig wurde (Tabellenzeile Q).
- **Instanzen mit dem Zufallsgenerator von Python statt SplitMix64.** Die festen Messreihen stammen aus Instanzen, die `random.Random` erzeugt; damit sie nachrechenbar bleiben, benutzt die Demo denselben Generator.

## Modell

- **Instanz:** eigene, Solomon-artige Instanzen, nicht die Originalinstanzen: Quadrat 100 × 100, Depot in der Mitte, Zeit = Entfernung, Bedienzeit 10, Horizont 300, Kapazität 70, Nachfrage 5 bis 25, Zeitfenster der Breite 20 bis 200 (Regler). Dazu das **Handbeispiel**:
  Depot (0, 0) und sieben Kunden auf einem Gitter, Manhattan-Abstand, Bedienzeit 2, Kapazität 6, Rückkehr bis 38, ganzzahlige Dualpreise.
- **Kreise:** Eine Route ist eine Besuchsfolge; **erlaubt** ist jede, in der nicht derselbe Kunde direkt nacheinander vorkommt (Gedächtnis k = 1, im Label steht nur der zuletzt besuchte Kunde; die Wiederkehr nach einem anderen Kunden, a-b-a, ist erlaubt); **elementar** ist jede, in der jeder Kunde höchstens einmal vorkommt.
  Jeder Besuch zählt Last, Bedienzeit, Fahrzeit und Dualpreis erneut; eine Spalte mit Kreis zählt einen mehrfach besuchten Kunden im Master mehrfach.
- **Master:** Überdeckung (jeder Kunde mindestens einmal), Start mit den Einzelfahrten Depot, Kunde, Depot; je Runde kommen bei Zufallsinstanzen bis zu 15, im Handbeispiel genau eine neue Spalte dazu.
- **Label und Dominanz:** Ein Label hat Zeit, reduzierte Kosten, Last und Gedächtnis; es dominiert ein anderes am selben Kunden, wenn Kosten, Zeit und Last höchstens so groß sind und sein Gedächtnis eine Teilmenge ist. Die Formeln und die Rechnung, warum die erste Runde Kreise anzieht, stehen im Expander „📐 Mathematische Formulierung“.

## Methodik

- **Experiment 1 (Handbeispiel, ein Pricing-Aufruf):** mit erlaubten Kreisen und elementar nebeneinander; Regler: Dualpreis von Kunde 7 (2 bis 14) und welche Regel Protokoll und Fahrplan zeigen. Label-Liste je Kunde, Protokoll jedes erzeugten Labels, bester Weg mit der Aufstellung
  „Entfernungen minus Dualpreise je Besuch“ und Fahrplan, Gegenprobe durch Aufzählung aller zulässigen Routen. Das Verdikt rechnet live, ob der beste Weg mit Kunde 7 mindestens zweimal besser ist als der beste elementare Weg.
- **Experiment 2 (Handbeispiel, ganze Spaltenerzeugung):** Runde für Runde, exakt mit Brüchen: Wert des Masters, neue Spalte mit Markierung „Kunde x mehrfach“, Endlösung mit der halben Kreisfahrt; daneben die elementare Rechnung und die Lücke. Gegenprobe: ein Master über alle zulässigen Routen.
- **Experiment 3 (Live-Rechnung):** zufällige Instanz mit 5 bis 20 Kunden und Fensterbreite 20, 40, 60, 100 oder 200: die ganze Spaltenerzeugung mit erlaubten Kreisen und elementar; Anteil der Spalten mit Kreis, beide Schranken, Lücke, Labels.
  Die elementare Rechnung bricht an einer festen Obergrenze ab (30 Millionen Dominanztests); dann zeigt die App „nicht erreicht“ statt einer Zahl. Jede neue Spalte wird vor der Anzeige unabhängig geprüft.
- **Experiment 4 (Welcher Kreis?):** kürzester Kreis (zwei, drei, vier oder mehr Kanten) und Wiederholungen je Kreis-Spalte, für die Instanz aus Experiment 3 neben der festen Messreihe (n = 30, Breite 40, 100 oder 200).
- **Experiment 5 (Messreihen):** (a) Anteil der Spalten mit Kreis und in der Endlösung gegen die Breite; (b) Lücke zur elementaren Schranke für n = 10 bis 30 und Breite 40 und 100, zu k = 8 (drei Instanztypen) und zu k = 16 (nicht neu gerechnet).
- **Kern:** `kip_algorithm.py` (Label-Setting, jede Regel eine Funktion) und `kip_master.py` (Master, Spaltenerzeugung); Kopie des Messkerns der Vormessung, umbenannt und in kleine Einheiten zerlegt. Messungen dieser README, nicht im Test (Scratch-Läufe, nicht im Repo):
  Die Zählungen erzeugter und dominierter Labels und die gefundenen Routen sind gleich denen des Messkerns in 900 Fällen (60 Zufalls-Seeds × 5 Kombinationen von n und Breite × 3 Gedächtnisse, nämlich 1, 5 und elementar bei n bis 16, sonst 1, 5 und 8; ein Pricing-Aufruf mit den Dualpreisen der ersten Runde);
  der Kern stimmt mit der Aufzählung (Orakel) in 1 600 Fällen überein (400 Gitterinstanzen × Gedächtnis 1, 2, 3 und elementar, dazu bei Gedächtnis 1 die überlebenden Labels gegen die Pareto-Front).

## Befunde (gemessen, keine Behauptungen)

„Mittel“ und „Maximum“ der Lücke gelten über die Instanzen mit fertiger Bezugsrechnung; die Zufalls-Seeds sind 0 bis 5 (6 Instanzen), bei den Zellen zu k = 8 0 bis 4 (5 Instanzen). Die Zahl der Spalten, Runden und Spalten mit Kreis ist auf einem Windows-Rechner mit HiGHS gerechnet und kann auf einem anderen
bei gleich guten Lösungen des Masters leicht abweichen; die Schranken tun das nicht (siehe Tests).

| Frage | Befund | Test |
|---|---|---|
| **Handbeispiel** (7 Kunden, Dualpreise der ersten Runde, Kunde 7: 10): Wie viele Labels und welcher beste Weg, mit erlaubten Kreisen und elementar? | Mit erlaubten Kreisen 62 erzeugte Labels (27 sofort verworfen, 5 später verdrängt), bester Weg 7 → 6 → 7 → 6 mit reduzierten Kosten 14 − 32 = −18 (Kunden 6 und 7 je zweimal); elementar 56 Labels, bester Weg 2 → 7 → 6 mit 12 − 22 = −10. Der Kreis macht den besten Weg um 8 günstiger. | A |
| Handbeispiel: Gegenprobe durch Aufzählung aller zulässigen Routen? | Mit erlaubten Kreisen 89 Routen, davon 10 mit Kreis (alle 10 mit negativen reduzierten Kosten), insgesamt 68 mit negativen reduzierten Kosten, bester Wert −18 wie im Labeling; elementar 79 Routen, bester Wert −10. | B |
| Handbeispiel: Wie hängt der beste Weg am Dualpreis von Kunde 7 (2 bis 14, übrige Dualpreise der ersten Runde)? | Bei allen 13 Werten enthält der beste Weg mit erlaubten Kreisen einen Kreis: bei 2 bis 8 ist es 5 → 3 → 5 → 1 mit −14 (bei 8 gleichauf mit 7 → 6 → 7 → 6), ab 9 ist es 7 → 6 → 7 → 6 mit 2 − 2·Dualpreis (−16 bei 9 bis −26 bei 14). Der beste Weg mit Kunde 7 mindestens zweimal ist besser als der beste elementare Weg ab Dualpreis 6 (bei 5 gleichauf mit −8), bei 2 bis 5 nicht. | C |
| Rechnung (keine Messung): Wie viel niedriger sind in der ersten Runde die reduzierten Kosten von 0-i-j-i-0 gegenüber 0-i-j-0? | Genau doppelt so niedrig, nämlich 2 (d(i, j) − d(0, i) − d(0, j)), wenn Last und Fenster beide Besuche von i erlauben. Im Handbeispiel für i = 7, j = 6: −12 gegen −6. | D |
| Handbeispiel, ganze Spaltenerzeugung: Wo endet sie mit erlaubten Kreisen, wo elementar? | Mit erlaubten Kreisen nach 8 Runden bei 83/3 (27,67); Master je Runde 50, 41, 33, 33, 32, 29, 28, 83/3; 7 neue Spalten, 4 mit Kreis (jeweils zwei Kanten); 416 Labels insgesamt; Endlösung mit Mengen 1/2 (7 → 6 → 7 → 6), 1 (2 → 1), 2/3 (3 → 4), 1/3 (5 → 3 → 5), 1/3 (5 → 4). Elementar nach 7 Runden bei 30 mit 326 Labels. Ein Master über alle 89 bzw. 79 zulässigen Routen gibt 83/3 bzw. 30. Lücke (30 − 83/3) / 30 = 7,78 %. | E |
| Handbeispiel: Warum ist der Master mit Kreis-Spalten billiger? | Die Spalte 7 → 6 → 7 → 6 (Kosten 14) hat Menge 1/2, kostet also 7 und überdeckt die Kunden 7 und 6 je einmal; die elementare Fahrt 7 → 6 durch dieselben Kunden kostet 10. | F |
| **Kleine Instanzen** (7 Kunden, Zufalls-Seeds 0 bis 59 mal Breiten 30, 80, 200 = 180 Fälle, zufällige Dualpreise gleichverteilt von 20 bis 70, ein Pricing-Aufruf): Wie oft liegt der beste Wert (0, wenn keine Route negative reduzierte Kosten hat) mit erlaubten Kreisen echt unter dem elementaren? | In 102 von 180 Fällen (56,7 %), in keinem darüber. Die Dualpreise sind Zufallszahlen, nicht die eines Masters; die Häufigkeit gilt nicht für echte Spaltenerzeugungen. Das elementare Labeling stimmt in allen 180 Fällen mit der Tiefensuche überein (Orakel-Test, siehe Tests). | G |
| **Anteil der Spalten mit Kreis** (n = 30, zufällig, erlaubte Kreise, Master HiGHS, 6 Instanzen je Breite): Wie groß ist er? | Unter den neuen Spalten: Breite 40: 62 von 1 108 (5,6 %); Breite 100: 865 von 1 206 (71,7 %); Breite 200: 1 175 von 1 320 (89,0 %). Unter den Spalten der Endlösung (Menge über 1e-9): 9 von 105 (8,6 %), 79 von 142 (55,6 %), 119 von 149 (79,9 %); Anteil an der Menge der Endlösung 4,9 %, 46,3 %, 69,0 %. | H |
| Dieselbe Reihe: Welcher Kreis ist es? | Kürzester Kreis mit zwei Kanten (i, j, i): 62 von 62 (Breite 40); 845 von 865 (97,7 %), dazu 20 mit drei Kanten (Breite 100); 1 104 von 1 175 (94,0 %), dazu 64 mit drei und 7 mit vier oder mehr Kanten (Breite 200). Wiederholungen je Kreis-Spalte bei Breite 100: 1: 519, 2: 240, 3: 82, 4: 16, 5: 6, 6: 2; mittlere Länge 4,89 Kunden je neuer Spalte, 5,24 je Kreis-Spalte. | I |
| Voreinstellung der Live-Rechnung (15 Kunden, Breite 100, Zufalls-Seed 0, eine Instanz): Was zeigt sie? | 55 von 76 neuen Spalten mit Kreis (72,4 %); Schranke 411,46 mit erlaubten Kreisen, 440,88 elementar; Lücke 6,67 %. | J |
| **Lücke zur elementaren Schranke** (zufällig, 6 Instanzen je Zelle, alle elementaren Läufe fertig): Wie groß ist sie in Abhängigkeit von n und Breite? | Breite 40, n = 10 / 15 / 20 / 25 / 30: Mittel 0,72 / 0,62 / 0,51 / 0,74 / 0,24 %, Maximum 4,33 / 2,71 / 2,56 / 1,47 / 0,72 %, Lücke null in 5 / 3 / 4 / 0 / 2 von 6 Instanzen. Breite 100: Mittel 5,45 / 4,47 / 4,42 / 3,98 / 3,33 %, Maximum 13,91 / 6,89 / 7,40 / 4,57 / 6,80 %, Lücke null in 1 / 0 / 0 / 0 / 0 von 6. | K |
| Dieselbe Reihe: In welchem Bereich liegen die mittleren Lücken? | Zwischen 0,24 und 5,45 %: bei Breite 40 in allen 5 Zellen höchstens 0,74 %, bei Breite 100 in allen 5 Zellen zwischen 3,33 und 5,45 %. Die Lücke des Handbeispiels (7,78 %, Zeile E) liegt über jedem dieser Mittel. | L |
| n = 30, Breite 100: Wie viele elementare Läufe wurden fertig, und was ändert das an der Lücke? | In der Messung vor dem Bau 3 von 6 (Zeitgrenze, mittlere Lücke 4,82 %), mit der Obergrenze von 600 Millionen Dominanztests in dieser Demo 6 von 6 (mittlere Lücke 3,33 %). | M |
| Dieselbe Reihe: Wie viele Labels braucht die ganze Spaltenerzeugung? | Median über 6 Instanzen (bei sechs Werten der Mittelwert der beiden mittleren), n = 30: Breite 40: 16 938,5 mit erlaubten Kreisen gegen 40 175 elementar; Breite 100: 57 329,5 gegen 186 957. In allen 10 Zellen (n = 10 bis 30, Breite 40 und 100) weniger Labels mit erlaubten Kreisen. | N |
| **Lücke zu k = 8** (n = 30, 5 Instanzen je Typ; zufällig und gruppiert Breite 100, „lang“ mit Horizont 500, Kapazität 120 und Breite 60; Bezug k = 8, weil die elementare Rechnung bei n = 30 oft zu lange dauert): Wie groß? | Mittel (Maximum): zufällig 3,56 % (6,80), gruppiert 4,37 % (7,12), lang 2,24 % (5,71); Lücke null in 0, 0 und 1 von 5 Instanzen. Die Lücke zur elementaren Schranke ist mindestens so groß (die Schranke sinkt mit wachsendem k nie). | O |
| **Lücke zu k = 16** (nicht neu gerechnet, nur aus der Auswertungsdatei der Messung vor dem Bau; 12 Instanzen je Zelle): Wie groß? | n = 50, Breite 100: gruppiert 2,518 % (Maximum 3,651), zufällig 3,227 % (4,811); n = 50, Breite 40: 0,845 % (2,378) bzw. 1,191 % (4,293); n = 100, Breite 40: 0,762 % (1,405) bzw. 0,879 % (1,528); n = 100, Breite 20: 0,000 % in 12 von 12 Instanzen, beide Typen. | P |
| Stimmen die neu gerechneten Schranken mit der Messung vor dem Bau überein? | In 147 verglichenen Schranken (Toleranz 1e-3, die Dateien nennen vier Stellen) 0 Abweichungen; die Summen der Spalten mit Kreis (62 von 1 108, 865 von 1 206, 1 175 von 1 320) sind gleich. | Q |

**Zahl → Test.** Die Zahlen der Tabelle stehen in `tests/test_claims.py` (exakt für das Handbeispiel und die Zählungen, aus den gespeicherten Rohwerten in `data/` für die Messreihen, mit den Auswertungsfunktionen der App); Ausnahmen: die Übereinstimmung des elementaren Labelings mit der Tiefensuche in Zeile G steht im Orakel-Test, die Aussage „wenn Last und Fenster beide Besuche erlauben“ in Zeile D im Eigenschaftstest:
A `test_hand_example_round_one_pricing_with_cycles_and_elementary`, B `test_hand_example_enumeration_counts`, C `test_hand_example_dual_price_of_customer_7_from_2_to_14`, D `test_hand_example_first_round_cycle_has_double_the_reduced_cost`,
E `test_hand_example_column_generation`, F `test_hand_example_half_cycle_trip`, G `test_180_cases_with_7_customers_k1_is_below_the_elementary_optimum_in_102_and_never_above`, H `test_share_of_cycle_columns_by_width`,
I `test_shortest_cycle_and_repetitions_per_cycle_column`, J `test_the_default_live_instance`, K `test_gap_to_the_elementary_bound_by_n_and_width`, L `test_the_gap_range_named_in_the_readme`,
M `test_n30_width_100_all_six_elementary_runs_finish_and_the_three_earlier_ones_had_the_larger_gaps`, N `test_labels_of_the_whole_column_generation_at_n_30`, O `test_gap_to_k8_for_three_instance_types`,
P `test_gap_to_k16_from_the_summary_file_not_recomputed`, Q `test_all_recomputed_bounds_agree_with_the_measurement_before_the_build`.
Die Messreihen in `data/` hat `tools/baender_erzeugen.py` mit dem Kern dieser Demo gerechnet; `tests/test_baender.py` rechnet Stichproben nach (Schranken auf 1e-6 relativ, Zahl der Spalten nur in Bändern, weil sie vom Master-Löser abhängt).
Nicht im Test, nur Messung dieser README (Scratch-Läufe, nicht im Repo): die 900 Vergleichsfälle des Kerns mit dem Messkern und die 1 600 Orakel-Fälle (siehe Methodik). Die Zeile P ist nicht neu gerechnet: der Test prüft nur, dass die gespeicherten Werte denen der Auswertungsdatei entsprechen.

## Ehrliche Grenzen

Dieselben Annahmen, Grenzen und bekannten Probleme wie im Expander „⚠️ Annahmen, Grenzen und bekannte Probleme“ der App (ein Test vergleicht beide Fassungen):

**Annahmen**

- Die Instanzen sind eigene, Solomon-artige Instanzen (Quadrat 100 × 100, Zeit = Entfernung, Bedienzeit 10, Horizont 300, Kapazität 70, Nachfrage 5 bis 25), zufällig verteilt, nicht die Originalinstanzen von Solomon. Das Handbeispiel hat sieben Kunden, ganzzahlige Entfernungen (Manhattan-Abstand), Bedienzeit 2, Kapazität 6 und Rückkehr bis 38.
- „Kreise erlaubt“ heißt: Verboten ist nur, denselben Kunden direkt nacheinander zu besuchen (Gedächtnis k = 1); sonst darf ein Kunde mehrfach vorkommen. Jeder Besuch zählt Last, Bedienzeit, Fahrzeit und Dualpreis erneut. „Elementar“ heißt: jeder Kunde höchstens einmal.
- Der Master ist ein Überdeckungs-Master (jeder Kunde mindestens einmal überdeckt); eine Spalte mit Kreis zählt einen mehrfach besuchten Kunden mehrfach. Gerechnet wird mit HiGHS (Zufallsinstanzen) und im Handbeispiel exakt mit Brüchen. Je Runde kommen bei Zufallsinstanzen bis zu 15 neue Spalten dazu, im Handbeispiel genau eine.
- Dualpreise sind die Preise, die der Master je Kunde vorgibt. In Experiment 1 sind es die Preise der ersten Runde (Hin- und Rückweg vom Depot, nur der von Kunde 7 ist einstellbar); in den Experimenten 2 bis 5 entstehen sie Runde für Runde aus dem Master.
- Gezählt werden erzeugte Labels und Dominanztests; Sekunden stehen nur zur Information da.

**Grenzen**

- Die festen Messreihen haben je Zelle 5 oder 6 Instanzen (Zufalls-Seeds ab 0), kein Konfidenzmaß; nur die Zeilen mit Bezug k = 16 haben 12 Instanzen.
- Gerechnet sind: der Anteil der Spalten mit Kreis bei n = 30 (Fensterbreite 40, 100 und 200); die Lücke zur elementaren Schranke bei n = 10 bis 30 (Breite 40 und 100, zufällig verteilt); die Lücke zur Schranke bei k = 8 bei n = 30 (zufällig, gruppiert und lang, je 5 Instanzen). Nicht gemessen sind die Lücke zur elementaren Schranke bei Breite 200, bei gruppierten und langen Instanzen und bei mehr als 30 Kunden.
- Die Zeilen mit Bezug k = 16 (n = 50 und 100) stammen nur aus einer Auswertungsdatei der Messungen vor dem Bau und sind mit dem Kern dieser Demo nicht neu gerechnet. Ein Bezug k = 8 oder k = 16 ist nicht die elementare Schranke: die Schranke sinkt mit wachsendem k nie (im Test an kleinen Instanzen nachgeprüft; sie steigt mit k), also ist die Lücke zu k = 8 oder 16 höchstens so groß wie die zur elementaren Schranke.
- Gezeigt wird nur der Preis der Kreise (die tiefere Schranke) und wie oft sie vorkommen; Verfahren, die Kreise teilweise oder ganz verbieten, sind außer der elementaren Rechnung nicht Gegenstand dieser Demo.
- Nur Vorwärts-Labeling und nur der Überdeckungs-Master.

**Bekannte Probleme und Unsicherheiten**

- Die elementare Rechnung der Live-Rechnung bricht an einer festen Obergrenze ab (30 000 000 Dominanztests in allen Pricing-Aufrufen zusammen); dann gibt es für diese Einstellung keine elementare Schranke und keine Lücke. Die Obergrenze zählt, sie misst keine Sekunden.
- Die Zahl der Spalten, der Runden und der Spalten mit Kreis hängt von den Dualpreisen des Master-Lösers ab: gibt es mehrere gleich gute Lösungen, kann HiGHS auf einem anderen Rechner andere Dualpreise liefern. Der Wert der Schranke hängt nicht davon ab (er ist der Wert der linearen Relaxation über alle zulässigen Routen). Die festen Messreihen sind auf einem Windows-Rechner gerechnet.
- Die Instanzen entstehen mit dem Zufallsgenerator von Python (`random.Random`), damit sie mit den festen Messreihen übereinstimmen; Stichproben der Messreihen werden in den Tests nachgerechnet.
- Erklärungen mit „weil“ sind Deutungen, soweit nicht ausdrücklich gemessen (zum Beispiel, warum bei engen Fenstern kaum Kreise vorkommen).
- Die Diagramme haben keine Auswahlfunktion; ein Mausklick auf sie bewirkt nichts.

## Tests

Die Suite hat 161 Tests (`pytest --collect-only -q tests`), alles unter `tests/`:

- **Kern** (`test_algorithm.py`): Erweiterungsregel (Last zuerst, Fenster, Warten, Grenzen inklusive, jeder Besuch zählt erneut), Dominanzregel, Einfügen, Rückverfolgung, Handbeispiel in allen Zahlen gegen Handrechnung (Rechnung in `tests/conftest.py`), Gegenprobe durch Aufzählung,
  beide Master gegeneinander (HiGHS und Brüche), Spaltenerzeugung Runde für Runde, Obergrenze, Hängetest am Regler-Maximum (n = 20, Breite 200).
- **Orakel** (`test_oracle_kreise_im_pricing.py`): unabhängige Aufzählung aller zulässigen Wege mit der Wiederholungsregel nach ihrer Definition; bester Wert bei Gedächtnis 1, 3 und elementar an 240 Fällen (80 Gitterinstanzen); bei Gedächtnis 1 die überlebenden Labels gegen die Pareto-Front;
  die Schranke der Spaltenerzeugung gegen einen eigenen Master über alle aufgezählten Routen; die 180 Fälle der Vorabmessung (elementares Labeling gegen Tiefensuche, 102 von 180).
- **Eigenschaften** (`test_eigenschaften_kreise_im_pricing.py`): die Schranke mit Kreisen liegt in 30 Instanzen nie über der elementaren und sinkt in 20 Instanzen nie, wenn das Gedächtnis wächst (k = 1, 2, 3, n); der beste Wert liegt in 60 Instanzen nie über dem elementaren; keine Route wiederholt einen Kunden direkt, jede Route ist zulässig;
  Umnummerieren der Kunden ändert Wert und Schranke nicht; Überdeckung gleich Partitionierung bei metrischen Kosten (elementar, und mit Kreisen im Handbeispiel); die doppelten reduzierten Kosten der Kreisroute in der ersten Runde; jede Regel wirkt auf mindestens einer Instanz; gleiche Zahlen in zwei Prozessen mit verschiedener Hash-Randomisierung.
- **Randfälle** (`test_edge_cases.py`): n = 1, n = 2 (kleinster Kreis, von Hand gerechnet), Last gleich Kapazität, Fenster ohne Spielraum, Kunden am selben Ort, Gleichstand, Dualpreise null, Horizont und Kapazität inklusive, kleinste Live-Instanzen.
- **Messreihen und Aussagen** (`test_baender.py`, `test_claims.py`, `test_verdicts.py`, `test_readme.py`): Aufbau und Stichproben der Messreihen, jede Zahl der README, jedes Verdikt mit Schwellen und Zahlen im Text, README gegen App-Text und Testzahl.
- **Oberfläche** (`test_app.py`, `test_layout.py`, `test_presets.py`, `test_footer.py`, `test_runtime_imports.py`): AppTest für Standard, jedes Beispielszenario (mit den erwarteten Verdikt-Zeilen), Permalink, jeden Regler an Minimum und Maximum und jede Auswahl; Schnellstart in der Seitenleiste mit hervorgehobenem Szenario;
  Footer; jeder Import steht in `requirements.txt`.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App: Einleitung, fünf Experimente, Annahmen, Mathematik |
| `data/baender_kreise.json` | Feste Messreihe: Anteil der Spalten mit Kreis (3 Breiten, 6 Instanzen je Breite; je Instanz neue Spalten, Spalten mit Kreis, Schranke, Endlösung, kürzester Kreis, Wiederholungen) |
| `data/baender_luecke.json` | Feste Messreihe: Lücke der Schranke (elementar, k = 8 neu gerechnet; k = 16 nur Zusammenfassung); je Zelle Quelle und Vergleich mit der Messung vor dem Bau |
| `kip_algorithm.py` | Kern: Gedächtnis, Erweiterung, Dominanz, Einfügen, Pricing `price`, Prüfer, Aufzählung, Kreise erkennen |
| `kip_baender.py` | Auswertung der festen Messreihen (Mittel, Maximum, Median, Zählungen) |
| `kip_constants.py` | Regler-Grenzen, feste Annahmen, Obergrenzen, Farben, Beispielszenarien |
| `kip_evaluation.py` | Läufe (Handbeispiel, Live), Protokoll, Verdikte als reine Funktionen, Zahlenformat |
| `kip_layout.py` | Fester Kopf (Stylesheet) |
| `kip_master.py` | Master (HiGHS und exakt mit Brüchen) und Spaltenerzeugung |
| `kip_presets.py` | Permalink (Begrenzen), Beispielszenarien (Schnellstart in der Seitenleiste, aktives Szenario hervorgehoben), Zufalls-Seed-Button |
| `kip_scenario.py` | Instanzen (Solomon-artig), Handbeispiel, Dualpreise der ersten Runde |
| `kip_texte.py` | Annahmen-Text (App und README), Tabelle „Wo die Annahmen enden“ und Formel-Expander |
| `kip_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `requirements-dev.txt` | Laufzeit plus pytest |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt) |
| `tools/baender_erzeugen.py` | rechnet die Messreihen in `data/` mit dem Kern neu und vergleicht sie mit der Messung vor dem Bau (falls erreichbar) |
| `tests/` | Kern, Orakel, Eigenschaften, Randfälle, Messreihen, Zahlen der README, Verdikte, Oberfläche, Footer, Laufzeit-Importe |

## Bewusst nicht umgesetzt

- **Verfahren gegen Kreise außer der elementaren Rechnung** (Gedächtnis über den zuletzt besuchten Kunden hinaus, Kreise bis zu einer Länge verbieten): nicht Gegenstand dieser Demo; hier steht nur der Preis der Kreise.
- **Partitionierungs-Master und geglättete Dualpreise:** nicht gerechnet (im Test nur: Überdeckung gleich Partitionierung bei metrischen Kosten an kleinen Instanzen).
- **Lücke zur elementaren Schranke bei Breite 200, bei gruppierten und langen Instanzen und bei mehr als 30 Kunden:** nicht gemessen; die elementare Rechnung ist dort zu aufwendig. Gruppierte und lange Instanzen stehen nur gegen k = 8, gruppierte und zufällige bei n = 50 und 100 nur gegen k = 16.
- **Bidirektionales Labeling, Eimer-Verfahren, Kantenstreichung:** nicht umgesetzt.
- **Zeit statt Labels als Messgröße:** Sekunden stehen nur zur Information.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

Lokal mit Python 3.14 geprüft, die CI läuft mit Python 3.12; die Python-Version der Streamlit Cloud wird beim Deploy eingestellt und ist hier noch nicht festgelegt.

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly, NumPy und SciPy.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zur Reihe: [Ressourcenwege: von der Grenze zur Verfahrenswahl](https://sebastianhanisch.net/konzepte-ressourcenwege.html).
