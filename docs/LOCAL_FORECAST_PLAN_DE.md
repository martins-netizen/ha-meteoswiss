# Lokalprognosepunkte: Katalog und Prognosequelle getrennt prüfen

**Planversion:** 1.0 · **Stand:** 20. Oktober 2026
**Status:** Dokumentierte Quellenprüfung und begrenzter Arbeitsplan.
Keine Laufzeitänderung, kein neuer Quellenadapter und keine HA-Installation.

## Entscheidung und Nutzen

Der offizielle MeteoSchweiz-Katalog soll vorrangig als Grundlage für die geplante
Suche nach PLZ, Ortschaft und Berg-POI untersucht werden. Für Nutzer zählt eine
eindeutige Auswahl mit verständlichem Namen, Ortstyp und belegter Höhe.
Ein Eintrag wird ausdrücklich als **Ort für die Wetterprognose** ausgewählt.

Die vorhandene App-Warnschnittstelle v3 bleibt bis auf Weiteres bestehen.
Der bestätigte Warnort bleibt separat konfiguriert. Gleiches gilt für die
Messstation und die Pollenmessstation. Ein Prognosepunkt verschiebt weder den
globalen HA-Standort noch diese anderen Bezüge.

Zwei Entscheidungen sind unabhängig:

1. **Katalog verwenden:** Ein belegter Prognoseort kann zunächst weiterhin
   Koordinaten für die vorhandene ICON-Seamless-Quelle liefern.
2. **Prognosequelle ändern:** Die aufbereiteten MeteoSchweiz-Lokalprognosen
   werden erst nach einer eigenen Machbarkeits- und Kompatibilitätsprüfung
   als Quelle erwogen. Der Katalog allein löst keinen Modellwechsel aus.

## Was am 20. Oktober 2026 belegt ist

| Befund | Quelle / Einordnung |
|---|---|
| Rund 6000 Prognosepunkte; Typ 1 = Station, 2 = PLZ, 3 = Berg-POI. Kennungen sind nur als Paar `point_type_id` + `point_id` eindeutig. | [Produktdokumentation](https://opendatadocs.meteoswiss.ch/e-forecast-data/e4-local-forecast-data) |
| Katalog mit Namen, Kennung, Höhe und Koordinaten; Prognoseparameter werden stündlich als Dateien für alle Punkte bereitgestellt. Stündliche Dateien können laut Dokumentation bis 33 MB pro Parameter erreichen. | Produktdokumentation; die Metadaten sind in der [STAC-Sammlung](https://data.geo.admin.ch/api/stac/v1/collections/ch.meteoschweiz.ogd-local-forecasting) verlinkt. |
| Aufbereitete Prognosen kombinieren INCA, ICON-CH1-EPS, ICON-CH2-EPS und ECMWF; laut Sammlung dieselbe Prognosegrundlage wie App und Website. | Beschreibung der STAC-Sammlung; kein Nachweis jederzeit identischer App-Anzeigen. |
| Der Anbieter zeigt Namens-/PLZ-Auswahl und Prognoseauswertung in einem eigenen Beispielprojekt. Das Prüfskript behandelt die Höhe als optional. | [Offizielles Beispielprojekt](https://github.com/MeteoSwiss/opendata-localforecast-demos) und [geprüfter Skriptstand](https://github.com/MeteoSwiss/opendata-localforecast-demos/blob/a75a153dcec3af619b5c7277c8da6c39fc767626/scripts/check_data_format.py) |
| Ein gezielter API-Zugang für Lokalprognosen wird für Ende 2026 als Beta vorbereitet. | [Anbieter-Roadmap](https://opendatadocs.meteoswiss.ch/general/roadmap); weder Verfügbarkeitszusage noch bereits verwendbarer Endpunkt. |

Die Produktdokumentation nennt neun Kalendertage einschliesslich heute; die
STAC-Beschreibung nennt +0 bis +192 Stunden. Der tatsächliche Zeitbereich pro
Punkt und Parameter muss im Versuch geprüft werden, statt 216 vollständige
Prognosestunden zu versprechen. OGD wird stündlich aktualisiert; die App kann
häufiger aktualisiert werden.

Der offizielle Katalog heisst
[`ogd-local-forecasting_meta_point.csv`](https://data.geo.admin.ch/ch.meteoschweiz.ogd-local-forecasting/ogd-local-forecasting_meta_point.csv).
Die [Parametermetadaten](https://data.geo.admin.ch/ch.meteoschweiz.ogd-local-forecasting/ogd-local-forecasting_meta_parameters.csv)
führen Einheiten und zeitliche Bedeutung.

**Grenze dieses Nachweises:** Produktdokumentation, STAC-Sammlungsmetadaten und
Anbieter-Prüfskript wurden gelesen. Die CSV-Rohdaten liessen sich mit dem
verfügbaren Webzugang wegen des CSV-Inhaltstyps nicht lesen. Ein weiterer
STAC-Item-Abruf war über diesen Zugang nicht erreichbar. Das belegt keinen
Anbieterausfall. Es wurden weder ein exakter aktueller Punktbestand noch
Prognosewerte, Dateigrössen, Prüfsummen der heruntergeladenen Dateien,
Laufzeit oder Speicherbedarf unabhängig gemessen. Der Anbieter-Skriptstand
belegt dessen erwartetes Format, keinen durch uns bestandenen Live-Test.

## L0: Katalog an vier öffentlichen Orten nachweisen

Die bisherigen Beispiele bleiben vergleichbar: **8302 Kloten, Säntis,
Gotthardpass und Albert-Heim-Hütte SAC**. Namen und Kennungen nicht aus alten
App-IDs ableiten. Zuerst das Vorhandensein im aktuellen offiziellen Katalog
prüfen. Fehlt ein Beispiel, ist das ein Ergebnis; keinen Nachbarpunkt still
als Ersatz übernehmen.

Nach einem begrenzten Download sind abzulegen: Abrufzeit in UTC, Quell-URL,
Payload-Grösse, SHA-256, erwartete Spalten, Zahl gültiger Punkte je Typ,
doppelte Kennungspaare und die vier ausgewählten Datensätze. Katalogstand und
Anbieter-Aktualisierungszeit nur übernehmen, wenn tatsächlich geliefert.
Koordinaten samt Referenzsystem, Einheit und Höhenbezug anhand der Metadaten
prüfen; keine LV03-/LV95-/WGS84-Zuordnung allein anhand einer Zahl vermuten.

Der Suchentwurf zeigt Name, PLZ soweit vorhanden, Typ und belegte Höhe.
Mehrdeutige Treffer brauchen eine Auswahl. Die offiziellen Typen belegen
nicht automatisch die Unterteilung eines einzelnen POIs in Gipfel, Pass oder
Hütte; eine solche Kategorie nur anzeigen, wenn sie zuverlässig ableitbar ist.
Höhe bleibt bei fehlendem Beleg unbekannt. Keine Schätzung aus einer Modellhöhe
als Gipfelhöhe ausgeben. Unicode-Namen, Akzente, leere Treffer, Duplikate,
unbekannte Typen und entfernte Punkte gehören zur Prüfung.

**L0 abgeschlossen, wenn:** Die vier Beispiele belegt oder fehlend dokumentiert
sind, Identität und Koordinatenvertrag feststehen und ein verständlicher
Trefferentwurf vorliegt. Ein App-POI-Katalogabruf ist kein zusätzliches Tor.

## L1: Aufwand und Datenvertrag der direkten Lokalprognosen prüfen

Zuerst den Katalog, dann nur die notwendigen Parameter für einen begrenzten
Vergleich laden. Der Parser soll den gewählten Punkt während des Lesens
filtern; keine dauerhafte Volltabelle aller Orte im HA-Arbeitsspeicher halten.
Zu messen sind tatsächliche Downloadbytes je Aktualisierung, Dauer,
Spitzenspeicher, Prozessorlast und ein hochgerechneter Tagesbedarf. Mehrere
konfigurierte Orte müssen dieselben Parameterdateien nach Möglichkeit teilen.

Der erste Vergleich deckt Temperatur, Wind/Böen, Niederschlag und Wettersymbol
sowie tägliche Minimal-/Maximaltemperatur ab. Für jedes aktuell genutzte
HA-Prognosefeld wird festgehalten: direkt vorhanden, fachlich korrekt ableitbar
oder nicht verfügbar. Eine fehlende Variable darf nicht still von einer zweiten
Prognosequelle ergänzt werden. Ein solcher Quellenmix wäre gesondert sichtbar
zu konzipieren.

Zeitauflösung und Aggregationsfenster bleiben Teil des Datenvertrags:
Intervallende, Momentanwert und lokaler Kalendertag unterscheiden; UTC und
Europe/Zurich einschliesslich Sommerzeitwechsel prüfen. Drei-Stunden-
Niederschlagswahrscheinlichkeit nicht als Ein-Stunden-Wahrscheinlichkeit
ausgeben. Wettersymbole brauchen eine eigene geprüfte HA-Zuordnung.
Offizielle MeteoSchweiz-Grafiken werden nicht übernommen.

Ein zeitgleich gespeicherter Vergleich an den vier Orten darf Abweichungen zu
Open-Meteo und zur offiziellen Anzeige erklären. Er beweist für sich allein
keine höhere Vorhersagegenauigkeit. Ohne Beobachtungen und geeigneten längeren
Vergleich keine Aussage «immer die akkurateste Prognose».

**L1 abgeschlossen, wenn:** Datensatz, Feldabdeckung, Zeitbedeutung und
Ressourcenbedarf belegt sind. Dann begründet zwischen direkter OGD-Nutzung,
Katalog mit bestehender Prognose oder Warten auf einen geeigneten Punkt-API-Zugang
entscheiden. Bandbreite und Pi-5-Ressourcen sind reale Entscheidungskriterien.

## L2: Standortvertrag und anschliessende Umsetzung

Das Standortmodell hält Provider, Punkt-Typ, Punkt-Kennung, Anzeigename,
Koordinaten mit Referenzsystem, optionale Höhe samt Herkunft und Katalogstand.
Interne Kennungen als undurchsichtige Werte behandeln; das Typ-/Kennungspaar
bleibt gemeinsam. Suchbegriffe sind keine dauerhafte Identität.

Ein Prognoseort ändert keine Messstation oder Warn-PLZ. Bestehende Einträge
behalten zunächst ihr Verhalten: Prognose am HA-Standort, Warnungen für die
bisher konfigurierte PLZ. Eine neue Auswahl wird bewusst vorgenommen.
Unveränderte Messquellen behalten Entity-/Unique-/Statistik-IDs; verschiedene
Stationshistorien werden nicht zusammengelegt.

Katalog und Prognose erhalten getrennte Lebenszyklen. Katalogsuche nicht bei
jedem Wetterrefresh wiederholen. Ein Suchdienstausfall darf bestätigte Orte
nicht unbrauchbar machen. Eine gültige gespeicherte Auswahl und ein letzter
gültiger Katalogstand dürfen mit erkennbarem Alter erhalten bleiben; fehlende
aktuelle Prognosen dürfen dadurch nicht als frisch gelten. Entfernte Kennungen
brauchen eine klare Meldung und erneute Auswahl, keinen stillen Ersatzpunkt.

Ein späterer Adapter übernimmt HA-eigene Session, TLS, feste HTTPS-Ziele,
Weiterleitungsprüfung, Timeout, Abbruch, begrenzte Retries und tatsächlich
erzwungene Antwortgrössenlimits. CSV mit belegter Latin1-Kodierung und
Semikolonformat prüfen; keine Ausführung von Inhalten. Diagnosen und Logs
enthalten keine privaten Suchbegriffe, Standort-URLs oder vollständigen
Rohantworten. Herkunft für Daten korrekt nennen.

**Umsetzung erst nach dem Quellenentscheid:** Kleine reguläre PRs für Katalog-
Client/Datenvertrag, übersetzte Auswahl und gegebenenfalls Prognoseadapter.
DE/EN/FR/IT und aussagekräftige Tests für Fehler, Duplikate, fehlende Höhen,
Zeitgrenzen, Cache, Migration und Entladen gehören dazu. HA-Forecast-
Verbraucher und vorhandene Automationen separat prüfen. Kein direkter
Produktivtest zur Katalogerkundung und keine Löschung bestehender HA-Einträge.

## Abgrenzung

Silver-/Gold-Arbeiten laufen unabhängig weiter. Die veröffentlichte Beta
`8.2.0b1`, ihre Betriebsabnahme und der bestätigte HACS-Wechsel werden durch
diese Planung nicht verändert. Die praktische Erstinstallation in einem leeren
System bleibt ein eigener offener Nachweis; der Anwender muss dafür keine
zweite dauerhafte HA-Umgebung bereitstellen.

Zurück zum [Entwicklungsplan](NEXT_RELEASE_PLAN_DE.md) und zum
[früheren POI-Teilnachweis](POI_FEASIBILITY.md).
