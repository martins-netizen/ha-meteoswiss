# Nächste Entwicklungsschritte: Ortsauswahl, Silver und Gold

**Planversion:** 1.1 · **Stand:** 17. Oktober 2026
**Status:** Freigegebener Plan; Q1 dokumentiert, P0 mit Teilnachweis. Keine Funktions-, Installations- oder Release-Freigabe.

Ziel ist eine verständliche Auswahl von Prognose- und Warnorten einschliesslich
POIs sowie ein nachvollziehbarer Weg zu den Silver- und später Gold-Anforderungen.
Ausgangspunkt ist `development` auf `137e41d`; dessen Laufzeitdateien entsprechen
dem geprüften Kandidaten `9c50b6b`. Die vorhandenen Nachweise bleiben in
[QUALITY_SCALE.md](QUALITY_SCALE.md) und im [Qualitätsreview](REVIEW_2026-10-17.md).

Die [HA-Qualitätsstufen](https://contributors.home-assistant.io/core/quality-scale/tiers/)
bauen aufeinander auf. Für diesen Custom-/HACS-Fork sind sie ein fachlicher
Massstab, kein vom HA-Projekt verliehener Titel. Ein bestandener HACS-Validator
ist ein eigener Nachweis. Erst nach vollständigem Einzelregel-Abgleich kann
eine dokumentierte Selbsteinschätzung «erfüllt die anwendbaren Silver-Kriterien»
erfolgen. Ausnahmen brauchen jeweils eine Begründung; ein `quality_scale`
Silver-/Gold-Eintrag oder entsprechendes Badge wird durch diesen Plan nicht eingeführt.

## Erster Umsetzungsschritt nach Freigabe

Plan V1.0 wurde am 17.10.2026 über [PR #25](https://github.com/martins-netizen/ha-meteoswiss/pull/25)
regulär nach `development` integriert (`6d74354`); alle PR- und Post-Merge-
Prüfungen waren erfolgreich. Der [vollständige Q1-Abgleich](QUALITY_AUDIT_2026-10-17.md)
liegt für alle 20 Bronze- und zehn Silver-Regeln vor. Konkrete Lücken sind
Feldhilfen/Intervallkonzept, gemeinsames Modul-Layout, optionales UV-Ausfallverhalten,
externer Brand-Nachweis und vier Module unter der geforderten Einzelabdeckung.
Die vorhandenen 762 Tests und 99,0517 % Gesamtcoverage ersetzen diese Lücken nicht.

Der [begrenzte P0-Versuch](POI_FEASIBILITY.md) belegt die öffentliche
swisstopo-Ortssuche und die bestehende ICON-Prognose für je einen Gipfel, Pass,
eine Hütte und Kloten als PLZ-Kontrolle. Er zeigt auch mehrdeutige Namen und
abweichende Standardhöhen. Aktueller App-Bezugsweg, vollständiger Warnungsbezug
und die definitive Höhenquelle bleiben offen. P0 ist deshalb nicht insgesamt
abgenommen; ein Standortkonzept kann auf dem dokumentierten Teilnachweis aufbauen.

Die V1.5-Befunde «Sicher/Unsicher», fehlendes Hasel-Symbol und optionaler UV-
Fehlerstatus gehören in getrennte Folgearbeiten. Die aktuelle Pollenquelle
liefert ausserdem Eiche als siebte Messart; der Fork bindet bisher sechs an. Weder diese noch die POI-Funktion
werden in die laufende R0-Abnahme gemischt.

## Reihenfolge und Entscheidungspunkte

| Paket | Inhalt | Fertig, wenn … | Abhängigkeit |
|---|---|---|---|
| R0 · Laufende Freigabe | Den bereits geprüften Kandidaten, zusammengehörige Warnungsanpassungen, Rückweg und tatsächlichen Betrieb abnehmen; Erstinstallation/HACS-Wechsel praktisch prüfen | Exakter Quellstand und HA-Version, grüne Prüfungen, Betriebsbeobachtung und HACS-Nachweise dokumentiert sind | Vor einer öffentlichen Versionsfreigabe; POIs erweitern diesen Kandidaten nicht |
| Q1 · Bronze-/Silver-Abgleich | Jede anwendbare Regel mit Code, Test und gegebenenfalls Praxisnachweis bewerten | Eine vollständige Lückenliste ohne pauschale «done»-Markierungen vorliegt | Kann jetzt rein lesend beginnen |
| S1 · Silver schliessen | Quellenverhalten, Lebenszyklus, verbleibende Modulabdeckung und verständliche Parameter abschliessen | Alle anwendbaren Bronze-/Silver-Regeln belegt, begründete Ausnahmen dokumentiert sind | Q1; Umsetzung als kleine PRs nach R0 |
| P0 · POI-Machbarkeit | Katalog, Kennungen, Punktprognose und Warnungszuordnung an drei Beispielen nachweisen | Ein Gipfel, ein Pass und eine Hütte reproduzierbar geprüft sind; unterstützte Daten und Grenzen feststehen | Kann unabhängig von R0 untersucht werden; keine Produktivänderung |
| P1 · Standort- und Bedienkonzept | Gemeinsame Suche, klarer Verwendungszweck und kompatible Standortdaten festlegen | Dialogentwurf, Datenvertrag und Migrationsfälle geprüft sind | P0; Gold-Nachkonfiguration mitplanen |
| P2 · POI-Funktion | Den bestätigten Umfang mit DE/EN/FR/IT, Tests und Hilfe umsetzen | Neue und bestehende Einträge sowie alle betroffenen Datenfamilien abgenommen sind | R0, S1 und P1; eigener Funktionsrelease |
| G1 · Gold vervollständigen | Nachkonfiguration, Darstellungsdetails, Diagnosen, handlungsbezogene Repairs und Dokumentation ausbauen | Auch die gesamte Gold-Matrix samt Bronze/Silver belegt ist | S1; auf denselben Standortvertrag wie P1/P2 aufbauen |

**Zeitlich:** Planung und begrenzte Quellenprüfung können sofort stattfinden.
Die laufende Freigabe behält ihre eigene Beobachtungszeit. Verbindliche Termine
oder Versionsnummern für S1/P2/G1 werden erst nach Q1 und P0 festgelegt.
Neue Produktivänderungen nicht während einer laufenden Abnahme vermischen.
P0 kann mit einem begründeten «derzeit nicht tragfähig» enden; Silver bleibt
davon unabhängig. Gold kann ebenfalls ohne POIs verfolgt werden.

## Q1/S1: Was für Silver konkret zu klären ist

Die [offizielle Regelübersicht](https://contributors.home-assistant.io/core/quality-scale/rules/)
ist die Prüfliste; die folgende Tabelle beschreibt unsere Arbeitspakete,
nicht bereits zugesprochene Erfüllung.

| Bereich | Ausgangspunkt und nächster Nachweis |
|---|---|
| Bronze als Voraussetzung | Alle 20 Regeln erneut einzeln abgleichen. Besonders gemeinsames Entity-/Coordinator-Layout, Feldbeschreibungen, Daten/Optionen und öffentliche Abhängigkeiten prüfen. Lokale HACS-Brand-Dateien nicht mit einer Aufnahme im Core-Brands-Repository gleichsetzen. |
| `action-exceptions` | Mangels eigener Integrationsaktionen ist eine begründete Ausnahme vorgesehen; bei späteren Aktionen neu bewerten. |
| `config-entry-unloading` | Vorhandene Recorder-/Reload-/Abbau-Tests erhalten; verbleibende Tasks, Poller und Listener je Datenfamilie gegenprüfen. |
| `docs-configuration-parameters`, `docs-installation-parameters` | Jedes Feld mit Zweck, Datenquelle und Auswirkungen erklären; Prognoseort, Messstation, Warnort und Pollenmessstation auseinanderhalten. |
| `entity-unavailable` | Jeden aktiven Entitypfad für Einzelwert fehlt / Quelle ausgefallen / veraltet / Erholung prüfen. Beobachtungen, Prognosen, Warnungen, Pollen, AQ/UV, Statistik und Diagnostik getrennt betrachten. |
| `integration-owner` | Eigentümer, Fork-Support und vertraulichen Meldeweg als aktuelle Nachweise führen. |
| `log-when-unavailable` | Einmalige Ausfall-/Erholungsmeldung über alle aktiven Quellen prüfen; Koordinaten, Ortskennungen, Nutzdaten und rohe Fehlerketten auch in Debug-Logs schützen. |
| `parallel-updates` | Vorhandene Plattformgrenzen mit tatsächlichen Abrufen und gleichzeitigen Refreshes abgleichen; keine überlappenden Zusatzabrufe einführen. |
| `reauthentication-flow` | Aktuelle öffentliche Quellen verwenden keine Zugangsdaten; Ausnahme belegen. Keine zusätzliche Anmeldung allein für die Qualitätsliste erfinden. |
| `test-coverage` | Mehr als 95 % **je Modul**, nicht nur im Gesamtwert, nachweisen; vorhandene strengere Zweig-/Flow-Prüfungen erhalten. |

**Konkreter Abdeckungsbefund:** Für den Laufzeitkandidaten bestehen 762 Tests
auf den bisherigen beiden HA-Prüfständen; ein zusätzlicher Lauf auf HA 2026.10.2
mit offiziellen Abhängigkeitsvorgaben misst **99,0517 % kombiniert**.
Trotzdem stehen `camera.py`, `hydro.py`, `slf.py` und `version.py` im Bericht auf
0 %; `const.py` liegt bei 98,51 %. Die drei inaktiven Produktplatzhalter brauchen
eine fachliche Entscheidung nach Referenzprüfung: bewusst aus dem ausgelieferten
Umfang entfernen oder tatsächlich sinnvoll implementieren und testen.
Die Versionsdefinition muss mit Manifest und Prüfskript konsistent bleiben.
Keine Coverage-Ausschlüsse und keine bedeutungslosen Tests allein für eine Zahl.
Lawinen-/Hochwasserwarnungen im gemeinsamen Warnungsclient bleiben unabhängig
von separaten SLF-/BAFU-Platzhaltern erhalten.

**Architektur:** Kein pauschaler Neubau. Die vorhandene Quellentrennung und
HA-eigene Session weiterverwenden. Wiederholte Entity-Grundfunktionen und die
[erwartete Modulstruktur](https://contributors.home-assistant.io/core/quality-scale/common-modules/)
gezielt prüfen; die bisherige Zentralisierung von Konstanten allein belegt
diese Regel noch nicht vollständig.

## P0/P1: Ortsauswahl und Verwendungszweck

Eine gemeinsame Namens-/PLZ-Suche mit anschliessender eindeutiger Trefferauswahl
ist das gewünschte Bedienmodell. POI-Treffer erhalten Kategorie und Höhe.
Anwender müssen keine internen App-Kennungen eingeben.

| Geplantes Feld | Erklärung direkt am Eingabefeld |
|---|---|
| **Ort für die Wetterprognose** | Für welchen Ort möchtest du die Wettervorhersage erhalten? Suche nach Postleitzahl, Ortschaft, Gipfel, Pass oder Berghütte. |
| **Wetterstation für Messwerte** | Diese Station liefert gemessene Werte wie Temperatur, Wind und Niederschlag. Sie kann vom Prognoseort abweichen. |
| **Ort für Naturgefahrenwarnungen** | Für diesen Ort werden die verfügbaren Wetter- und Naturgefahrenwarnungen abgefragt. |

Ein bestätigter gemeinsam verwendbarer Ort kann vorgeschlagen werden; eine
abweichende Warnungszuordnung muss sichtbar bestätigt werden. Die separat
gewählte Pollenmessstation bleibt als solche erklärt. Hilfetexte gehören
in die übersetzbaren Dialogfelder, nicht nur in die README.

**Vorhandene Grundlage:** Im signaturgeprüften Android-App-Paket 3.6.0 enthält
der eingebettete Katalog 181 insgesamt 623 POIs: 335 Gipfel, 205 Hütten und
83 Pässe. Der Katalog enthält Kennungen, Namen/Aliase, Schweizer Gitterkoordinaten,
Höhen und viersprachige Kategorien. Diese Zahl beschreibt den eingebetteten
Startbestand. [swisstopo bestätigt](https://www.swisstopo.admin.ch/en/faq-swisstopo-application-base-map)
MeteoSchweiz-Lokalprognosen für ausgewählte Gipfel, Pässe und Hütten.
Ein einzelner Abruf der App-Katalogdatei wurde mit HTTP 403 abgewiesen;
aktueller zulässiger Katalogbezug und konkrete POI-Aufrufe bleiben offen.
Es gibt noch keinen vollständigen POI-Abrufnachweis und keine Umsetzung.

**P0-Abnahme:** Je ein Gipfel, Pass und eine Hütte, dazu eine bekannte PLZ als
Kontrolle: Kennung, Koordinatenumrechnung, Höhe, Zeitpunkt und Prognoseumfang
mit dem Anbieter vergleichen; aktive/angekündigte Warnungen und ihre tatsächliche
räumliche Gültigkeit prüfen. Tests für leeren/defekten/veralteten Katalog und
nicht unterstützte Daten gehören dazu. Keine aus alten nackten Regionsnummern
abgeleitete Vollständigkeit und keine still ersatzweise verwendete Nachbar-PLZ.
Bei unzureichender Warnabdeckung getrennte bestätigte Warnort-Auswahl vorsehen;
«nicht unterstützt» ist keine Entwarnung. Drittanbieter-Daten nur mit geklärter
Nutzungsgrundlage übernehmen; kein APK oder dekompilierter Fremdcode im Fork.

**P1-Datenvertrag:** Ortstyp, Providerkennung, Anzeigename, Koordinaten,
Koordinatensystem, Höhe, Herkunft und unterstützte Daten getrennt modellieren.
POI-Kennungen sind keine PLZ; kein pauschales Anhängen von `00`.
Prognose- und Warnungsclients lösen diese Standorte über eigene Adapter auf.
Ein Modellwechsel zu App-Punktprognosen ist ein expliziter Quellenentscheid;
die bestehende ICON-Seamless-Quelle nicht still ersetzen.

**Bestandsschutz:** Bei MeteoSwiss-Stations-Einträgen kommt der Prognoseort heute
vom HA-Standort, während die eingegebene PLZ den Warnort bestimmt. Alte Einträge
müssen dieses Verhalten zunächst behalten. Keine automatische Interpretation
der alten Warn-PLZ als neue Prognoseauswahl; globale HA-Koordinaten nicht ändern.
Ein Wechsel des gemessenen Stationsorts braucht eine ausdrückliche Prüfung der
Zeitreihenbedeutung; verschiedene Stationen nicht unbemerkt in derselben
Messhistorie vermischen. Unveränderte Quellen behalten ihre vorhandenen IDs,
Statistiken und Nutzeranpassungen. Duplikate, Rückweg und Änderungen des
Standortvertrags werden vor dem Flow-Code festgelegt.

## G1: Gold-Arbeitspakete

Die 21 Gold-Regeln werden im Einzelregel-Abgleich geführt. Die Bündel unten
stellen die Umsetzung zusammen; «vorhanden» bedeutet weiterhin «zu bestätigen».

| Bündel / zugehörige Regeln | Geplantes Ergebnis |
|---|---|
| `devices`, `dynamic-devices`, `stale-devices` | Bestehende Quellen-/Gerätegruppierung und stabile Identitäten nachvollziehbar; Änderungen im Stations-/POI-Katalog fachlich prüfen, keine historischen Entitäten ungefragt löschen. Anwendbarkeit dynamischer Geräte einzeln begründen. |
| `diagnostics` | Vorhandene geschwärzte Diagnose um hilfreiche Quellen-/Standortzustände ergänzen, ohne private Orte oder Rohantworten offenzulegen; echte HA-Downloadroute testen. |
| `discovery`, `discovery-update-info` | Für einen öffentlichen Cloud-Dienst je Regel begründete Anwendbarkeit/Ausnahme festhalten. Ortssuche ist keine Netzwerk-Geräteerkennung. |
| `entity-category`, `entity-device-class`, `entity-disabled-by-default` | Sensoren fachlich klassifizieren; selten benötigte Helfer angemessen vorbelegen. Bewusste bestehende Benutzerentscheidungen erhalten. |
| `entity-translations`, `exception-translations`, `icon-translations` | Harte englische Namen/Fehler und Icons gezielt prüfen, unter anderem Stations-/Cache-Diagnose und Warnsensoren. DE/EN/FR/IT, Feldhilfen und künftig `icons.json` konsistent prüfen; fertige Sprachdateien allein sind kein kompletter Gold-Nachweis. |
| `reconfiguration-flow` | Vorhandenen Eintrag mit vorausgefüllten, validierten Werten bearbeiten; Quellenidentität, Duplikate, Statistikbedeutung und Reload beachten. Ein Optionsdialog allein ersetzt diesen Nachweis nicht. Mit P1 denselben Standortvertrag nutzen. |
| `repair-issues` | Nur behebbare Konfigurationsprobleme mit klarer übersetzter Handlung melden; nach Behebung entfernen. Vorübergehende Anbieter-Ausfälle über Verfügbarkeit/Logs behandeln. |
| `docs-data-update`, `docs-examples`, `docs-known-limitations`, `docs-supported-devices`, `docs-supported-functions`, `docs-troubleshooting`, `docs-use-cases` | Aktualisierung/Quelle, unterstützte Orte/Daten und Grenzen vollständig abgleichen; kurze Wetter-/Warnungs-/Pollenbeispiele und einfache Fehlerhilfe. Einsteiger führen Neueinrichtung/Wechsel durch, erfahrene Nutzer prüfen Attribute und Quellen. |

## Sicherheits- und Wartungsarbeiten

Den bereits identifizierten Härtungsauftrag neben S1 führen: gemeinsame
HTTPS-/Ziel-/Weiterleitungsprüfung und Grössenlimits für Quellenantworten,
einschliesslich späterem POI-Katalog. Zugriffe mit Timeout, Abbruch und
sparsamem Cache; Fehlertexte und Diagnose ohne private Suchbegriffe.
Für fremde Fork-Beiträge eine sichere CodeQL-Prüfroute planen; keine
privilegierte Ausführung fremden Codes. Diese Punkte als eigene kleine PRs
bewerten, keine nachträgliche Sammeländerung im laufenden Release-Kandidaten.

## Vorgeschlagene PR-Folge und gemeinsame Abnahme

| Reihenfolge | Umfang des späteren PRs | Prüfkriterium |
|---|---|---|
| 1 | Regelmatrix und Bronze-Restpunkte präzisieren | Für jeden Punkt Status, Evidenz, Lücke oder begründete Ausnahme |
| 2 | Gezielte Struktur-/Umfangsbereinigung und echte Abdeckungslücken | Öffentliche Referenzen geprüft; keine Funktion verloren; je Modul >95 %, bestehende strengere Gates erhalten |
| 3 | Noch offene Silver-Ausfall-/Erholungs- und Lebenszykluspfade | Gezielte Regression vor Änderung reproduziert, nach Änderung bestanden |
| 4 | Bestätigten POI-Datenvertrag und Quelladapter umsetzen | P0-Belege, typisierte Standortdaten, Datenschutz und Fehlerfälle |
| 5 | Gemeinsame Suche, Zwecktexte und Nachkonfiguration | Native HA-Flows, Bestandsschutz und DE/EN/FR/IT |
| 6 | Verbleibende Gold-Darstellung, Diagnose, Repairs und Dokumentation | Gesamte Regelmatrix und praktischer Anwenderdurchlauf abgeschlossen |

PRs dürfen kleiner geschnitten oder nach Q1 angepasst werden. Jeder Laufzeit-PR
braucht passende Regressionen und die unterstützten HA-Prüfstände; vor einem
Release zusätzlich den dann aktuellen HA-Patch prüfen. Änderungen regulär in
das geschützte `development` integrieren; `tests`, `Analyze Python` und
`HACS validation` behalten. Erst danach einen geprüften Installer/Kandidaten
übernehmen. Reine Dokumentationsmerges erfordern keine HA-Neuinstallation.

Eine zweite dauerhafte HA-Installation beim Anwender wird nicht vorausgesetzt.
Für Erstinstallation und HACS-Quellenwechsel ist ein temporärer isolierter
Durchlauf vorzubereiten; automatisierte HA-/Recorder-/Flow-Tests liefern schon
jetzt reproduzierbare Nachweise. Ein vollständiger HACS-Oberflächendurchlauf
steht noch aus. Reale Geräte während der Prüfung nicht ansteuern.

**Unmittelbar nächste Planungsarbeit:** Q1 in eine vollständige belegte Matrix
überführen und P0 als begrenzten Quellenversuch spezifizieren. Fachliche Entscheidungen
zu POI-Warnabdeckung, Katalogpflege und Stationswechsel vor der Implementierung
abschliessen. Gold bleibt das Folge-Ziel nach nachgewiesenem Silver.
