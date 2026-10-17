# POI-Machbarkeit: erster Quellenversuch

**Dokumentversion:** 1.0 · **Stand:** 17. Oktober 2026
**Ergebnis:** Namenssuche und koordinatenbasierte Prognose positiv erprobt;
aktueller App-Katalog und POI-Warnabdeckung noch nicht vollständig belegt.
Keine POI-Funktion ist dadurch bereits implementiert oder freigegeben.

Die [Planung](NEXT_RELEASE_PLAN_DE.md) sieht drei Beispiele und eine PLZ-Kontrolle
vor. Der Versuch zeigt einen Weg über die dokumentierte öffentliche
swisstopo-Suche und die bereits verwendete Open-Meteo-/MeteoSwiss-ICON-Quelle.
Ein Zugriff auf geschützte App-Dienste ist dafür nicht erforderlich. Die
Naturgefahrenwarnungen müssen weiterhin einen gesondert bestätigten Bezug haben.

## 1. App-Katalog als statischer Nachweis

Im zuvor signaturgeprüften Android-Paket MeteoSchweiz 3.6.0 liegt
`assets/localdata.sqlite`, eingebettete Katalogversion 181. Die Tabelle `poi`
enthält 623 Einträge: 335 Gipfel, 205 Berghütten und 83 Pässe. Sie enthält eigene
POI-IDs, Namen, Schweizer Gitterkoordinaten, Höhen, `warnregion`, Aktivkennzeichen
und Kategorien in DE/FR/IT/EN. Das ist der eingebettete Startbestand, kein
Nachweis eines aktuellen Live-Katalogs oder einer vollständigen Warnabdeckung.

| Beispiel | App-POI-ID | App-x / App-y | App-Höhe | App-`warnregion` |
|---|---:|---|---:|---:|
| Säntis, Gipfel | 711 | 744170 / 234918 | 2502 m | 168 |
| Gotthardpass, Pass | 594 | 686073 / 157063 | 2107 m | 302 |
| Albert-Heim-Hütte SAC, Berghütte | 454 | 678517 / 162475 | 2542 m | 149 |

Die nackten Regionswerte belegen weder ihre aktuelle räumliche Bedeutung noch
die Abdeckung von Hochwasser, Lawinen, Trockenheit und anderen Warnfamilien.
POI-IDs sind keine Postleitzahlen; das bisherige PLZ-Suffix `00` ist nicht auf
sie übertragbar. Die spätere Koordinatenübernahme braucht ein eindeutig belegtes
Koordinatensystem. Für den folgenden Netzversuch wurden deshalb direkt die
WGS84-Koordinaten der öffentlichen Suche verwendet, nicht diese Gitterzahlen.

Nachvollziehbarkeit des untersuchten Pakets:

- APK-SHA256: `a76f4a1bc8fbd41509e0fc43cf0a08c9f0ce27e802def596d4c15939bae6082a`
- Signaturzertifikat-SHA256: `07dbd58510fa5a8d7f02aafa88960dac64508a26a3b29fabf5d5a26e95490b60`
- SQLite-SHA256: `812f4eed10ee97a7deb6d237cef88582ae706e570b9d63d7bbfab668db586ed3`

Nur diese Befunde werden dokumentiert; APK, vollständige App-Datenbank und
dekompilierter Fremdcode werden nicht im Fork mitgeliefert. Die ergänzende
statische Prüfung aller drei DEX-Dateien erbrachte keinen vollständigen,
belegten POI-Abrufvertrag. Das untersuchte Paket enthält keine `.so`-Bibliotheken;
eine Vollständigkeit aller App-Implementierungsteile wird nicht behauptet.
Der einmalige frühere Abruf von `app-prod-static.meteoswiss-app.ch/v1/db.sqlite`
lieferte HTTP 403. Es gab keinen weiteren Abrufversuch mit veränderten Identitäten
oder Zugangsdaten. Dieser aktuelle App-Bezugsweg bleibt offen.

## 2. Öffentliche Namens-/PLZ-Suche

[GeoAdmin Search](https://docs.geo.admin.ch/access-data/search.html) dokumentiert
`SearchServer` mit `type=locations`, `origins=gazetteer` bzw. `zipcode`,
`sr=4326` und einer begrenzten Trefferzahl. Am 17.10.2026 wurden vier Suchbegriffe
und einmal eine grössere Trefferzahl für Säntis abgefragt: insgesamt fünf GETs,
keine Anmeldung und kein Katalog-Massendownload.

| Ausgewählter Treffer | WGS84 Breite / Länge | Befund zur Auswahl |
|---|---|---|
| Säntis · alpiner Gipfel · AI | 47.249424 / 9.343241 | Die ersten fünf Ergebnisse enthielten andere gleichnamige Orte; der Gipfel erschien erst in der erweiterten Liste mit 34 Treffern. |
| Gotthardpass · Pass · TI | 46.559311 / 8.561156 | Zwei unterschiedlich bezeichnete Suchtreffer mit identischen Koordinaten. |
| Albert-Heim-Hütte SAC · Gebäude · UR | 46.608932 / 8.463569 | Zwei nahe Gebäudetreffer, die Auswahl darf nicht allein nach dem Namen erfolgen. |
| 8302 Kloten · PLZ | 47.458755 / 8.582091 | Eindeutige PLZ-Kontrolle; Orts-/PLZ-Zentrum ist nicht automatisch der HA-Standort. |

**Folgerung für die Bedienung:** Nie automatisch den ersten Namensfund nehmen.
Kategorie, Kanton/Gemeinde und gegebenenfalls Höhe anzeigen; Nutzer wählen den
konkreten Ort. Treffer begrenzen, Suchauslösung entprellen und Ergebnisse cachen.
HTML-Markierungen aus `label` nur als Text aufbereiten. Die dokumentierte
Suchergebnis-`id` ist intern und darf nicht als dauerhafte Ortskennung gespeichert
werden. Einen stabilen Feature-Bezug nur verwenden, wenn der Dienst ihn liefert;
ansonsten bestätigte Koordinaten und Herkunft im eigenen Standortvertrag halten.
Die Suchantwort allein liefert noch keine belastbare Gipfelhöhe.

Datenquelle: © Data: swisstopo. Die
[Nutzungsbedingungen](https://www.geo.admin.ch/en/general-terms-of-use-fsdi)
sehen registrierungsfreie Nutzung mit Fair Use und die jeweiligen
Datensatzbedingungen/Quellenangaben vor. Für die Veröffentlichung des Features
sind Suchlast, Quellenhinweise und konkreter Datenumfang noch festzulegen.

## 3. Bestehendes Prognosemodell mit den Testkoordinaten

Mit exakt `models=meteoswiss_icon_seamless`, drei Prognosestunden und vier
Variablen wurden die drei Orte sowie Kloten geprüft. Alle vier GETs lieferten
am **17.10.2026 gegen 17:19 Uhr MESZ HTTP 200**, drei aufeinanderfolgende Stunden
und je drei endliche Werte für Temperatur, Niederschlag, Windgeschwindigkeit und
Wettercode. Das ist ein begrenzter Erreichbarkeits-/Datenvertragsnachweis;
weder ein Genauigkeitsvergleich noch ein vollständiger Fünf-Tage-/HA-Test.
Die [MeteoSwiss-ICON-Dokumentation](https://open-meteo.com/en/docs/meteoswiss-api)
beschreibt die Quelle. Es wurde kein Modellwechsel zur App-Punktprognose gemacht.

| Ort | Höhe im App-Katalog | Standardhöhe der Prognoseantwort |
|---|---:|---:|
| Säntis | 2502 m | 2399 m |
| Gotthardpass | 2107 m | 2108 m |
| Albert-Heim-Hütte SAC | 2542 m | 2518 m |
| Kloten, PLZ-Kontrolle | nicht übernommen | 442 m |

Das zurückgegebene Koordinatenpaar gehört zum Modellgitter und darf nicht den
gewählten Ort überschreiben. Gerade auf Gipfeln ist die Standardhöhe nicht
zwingend die Gipfelhöhe. Open-Meteo
[dokumentiert `elevation`](https://open-meteo.com/en/docs#api-documentation)
für die Höhenanpassung. Ein fünfter Prognose-GET für Säntis mit
`elevation=2502` lieferte HTTP 200, drei Stunden und die gewünschte Höhe 2502 m.
Damit ist die technische Vorgabe möglich, aber weder eine unabhängige Bestätigung
der Kataloghöhe noch eine Verbesserung der Prognosegenauigkeit bewiesen.
Höhenquelle, Einheit, Validierung und Cache-Schlüssel müssen vor Umsetzung zum
Standortvertrag gehören. Die Höhe darf nicht nur dekorativer Anzeigetext sein.

Die kompakte [Versuchsevidenz](evidence/poi_probe_2026-10-17.json) hält Abrufzeit,
öffentliche Request-URLs, gewählte Orte, Antwortgitter, endliche Wertezahlen und
Hashes der lokalen Mitschnitte fest. Sie enthält keine privaten HA-Koordinaten,
Kontodaten oder App-Zugangsdaten. Prognosewerte und Suchrankings ändern sich;
eine Wiederholung muss deshalb den Vertrag prüfen, nicht identische Wetterwerte.
Wetterdaten: MeteoSwiss via Open-Meteo.

## 4. Entscheidung und noch notwendige Nachweise

**Tragfähiger Kandidat für P1:** Die dokumentierte öffentliche Ortssuche kann
einen bestätigten Prognoseort liefern; das bestehende ICON-Modell kann die
Koordinaten verwenden. Der App-Katalog ist eine ergänzende Evidenzquelle und
muss nicht als ausgelieferte Datenbank vorausgesetzt werden. Diese Quellenwahl
ist vor der Feature-Umsetzung ausdrücklich festzuhalten.

**P0 ist noch nicht vollständig abgenommen:** Der konkrete aktuelle App-POI-
Prognoseabruf und die Warnungszuordnung der drei Beispiele sind nicht belegt.
Weder Suchtreffer noch ein erfolgreicher Forecast-GET beweisen Naturgefahren-
abdeckung. Keine automatische Nachbar-PLZ oder Übernahme der alten Regionszahl.
Bei getrenntem Warnort muss dieser sichtbar bestätigt werden; fehlende
Unterstützung bleibt als solche sichtbar und darf nicht «keine Warnung» ergeben.

Vor einem Feature-PR bleiben folgende Arbeiten:

1. Höhen-/Standortquellen und deren Nutzungsumfang festlegen; Mehrdeutigkeit,
   doppelte Treffer, Unicode, leere/defekte Antworten und Dienstausfälle behandeln.
2. Warnabdeckung je Beispiel und Warnfamilie reproduzierbar nachweisen oder
   den separat bestätigten Warnort ausdrücklich zum unterstützten Umfang machen.
3. Typisierten Standortvertrag und Ablaufentwurf erstellen: Prognoseort,
   Messstation und Warnort getrennt; bestehende Einträge unverändert übernehmen.
4. Datenvertrag mit dauerhaft gespeicherten bestätigten Koordinaten und
   Quellen-/Höhenmetadaten definieren. Suchdienst-Ausfall darf bestehende
   Prognosen nicht unnötig abschalten. Keine neue Suche bei jedem Wetterrefresh.
5. DE/EN/FR/IT, gezielte Fehler-/Migrations-/Lifecycle-Tests, gesamte Pflicht-CI
   und praktische HA-Sichtprüfung planen. Erst nach R0 und S1 implementieren.

Silver-Arbeit bleibt von diesen offenen POI-Fragen unabhängig.
