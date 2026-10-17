# Bronze-/Silver-Abgleich vom 17. Oktober 2026

**Dokumentversion:** 1.0 · **Status:** Q1 abgeschlossen; Umsetzungslücken offen.
**Geprüfter Stand:** `6d743546c8d0187a8bc91f870e8c50b3e7294147` auf `development`.
Die Laufzeitdateien, Sprachdateien und Tests entsprechen unverändert `9c50b6b`.

Der Fork hat eine weitgehend belegte technische Grundlage. Eine vollständige
Silver-Selbsteinschätzung ist noch nicht gerechtfertigt. Besonders Dialoghilfen,
die konfigurierbare Abrufperiode, das gemeinsame Entity-/Coordinator-Layout,
optionale UV-Ausfälle und vier Module unter der Mindestabdeckung bleiben offen.
Das ist eine Prüfung des Entwicklungsstands und keine Aussage über eine neu
installierte HA-Version. Die laufende Betriebs-/HACS-Abnahme bleibt eigenständig.

Die [offizielle Übersicht](https://contributors.home-assistant.io/core/quality-scale/rules/)
enthält 20 Bronze- und zehn Silver-Regeln. **Belegt** meint den in dieser Prüfung
beobachteten Code-, Test- oder Dokumentationsnachweis. **Teilweise/offen** nennt
einen konkreten fehlenden Nachweis. **Ausnahme** wird nur mit der in der Regel
vorgesehenen fachlichen Begründung verwendet. Der Vergleich mit Core-Regeln
verleiht einer Custom-/HACS-Integration keinen offiziellen Qualitätsgrad.
Bei Dokumentationsregeln dienen die Fork-eigenen Anleitungen als Massstab;
eine Aufnahme in die offizielle Core-Dokumentation wird damit nicht behauptet.

## Bronze: alle 20 Regeln

| Regel | Bewertung | Konkreter Nachweis und Restarbeit |
|---|---|---|
| [action-setup](https://contributors.home-assistant.io/core/quality-scale/action-setup/) | Ausnahme | Keine eigenen Integrationsaktionen; keine Registrierung von Services in `__init__.py` oder den aktiven Plattformen. `weather.get_forecasts` ist eine HA-Plattformaktion. |
| [appropriate-polling](https://contributors.home-assistant.io/core/quality-scale/appropriate-polling/) | Teilweise/offen | Provider-Abrufe laufen über begrenzte Coordinator-Intervalle, Beobachtungen mindestens 600 Sekunden. `config_flow.py` fragt jedoch `update_interval` ab. Die aktuelle Regel verlangt eine Entwicklerentscheidung statt eines Flow-Feldes. Bestehende Werte vor einer Änderung auf Kompatibilität prüfen. |
| [brands](https://contributors.home-assistant.io/core/quality-scale/brands/) | Teilweise/offen | Lokale HACS-Icons in `brand/` vorhanden und geprüft. Der für die Core-Regel genannte Pfad `home-assistant/brands/core_integrations/meteoswiss` lieferte am Prüftag HTTP 404. Lokale Assets erfüllen diesen externen Core-Nachweis nicht; kein ungeprüfter Brand-PR und kein offizielles Badge. |
| [common-modules](https://contributors.home-assistant.io/core/quality-scale/common-modules/) | Teilweise/offen | `const.py`, `runtime_data.py` und `weather_data.py` teilen Verträge. Es gibt noch keine gemeinsame `entity.py`; Coordinator-Klassen stehen auch in Plattform-/Quellenmodulen. Wiederholte Basisfunktionen und erwartetes Modul-Layout gezielt bereinigen, ohne die Quellentrennung neu zu bauen. |
| [config-flow](https://contributors.home-assistant.io/core/quality-scale/config-flow/) | Teilweise/offen | Native Einrichtung/Optionen, Validierung und Duplikatschutz vorhanden. Alle vier Sprachdateien haben für die sichtbaren Felder noch keine `data_description`. Selectorwahl sowie `data`/`options` zusammen mit dem Intervallfeld abschliessend prüfen. |
| [config-flow-test-coverage](https://contributors.home-assistant.io/core/quality-scale/config-flow-test-coverage/) | Belegt | `tests/test_config_flow.py`: beide Quellen, Fehler/Korrektur, Katalog-Retry, Gesamttimeout/Cancellation, alte und neue Duplikate, Optionen mit erhaltener Identität. `config_flow.py` hat 100 % Zeilen-/Zweigabdeckung und eine CI-Pflichtprüfung. |
| [dependency-transparency](https://contributors.home-assistant.io/core/quality-scale/dependency-transparency/) | Ausnahme | `manifest.json` hat `requirements: []`: keine zusätzlichen Python-Laufzeitabhängigkeiten der Integration. Von HA bereitgestellte Bibliotheken bleiben HA-Abhängigkeiten. Dokumentierte Internet-/Providerabhängigkeiten sind ein anderer Sachverhalt. |
| [docs-actions](https://contributors.home-assistant.io/core/quality-scale/docs-actions/) | Ausnahme | Keine eigenen Aktionen. `USAGE.md` erklärt diese Abgrenzung und die normale HA-Forecast-Aktion. |
| [docs-conditions](https://contributors.home-assistant.io/core/quality-scale/docs-conditions/) | Ausnahme | Keine eigenen Integrations-/Gerätebedingungen. `USAGE.md` verweist auf die normalen HA-Zustandsbedingungen. |
| [docs-high-level-description](https://contributors.home-assistant.io/core/quality-scale/docs-high-level-description/) | Belegt | README erklärt Nutzen, Datenfamilien, Herkunft und Grenzen; separates Angebot für Einsteiger und erfahrene HA-Nutzer. |
| [docs-installation-instructions](https://contributors.home-assistant.io/core/quality-scale/docs-installation-instructions/) | Belegt; Praxis separat offen | README, `START_DE.md`, `WECHSEL_DE.md` und `USAGE.md` dokumentieren Neuinstallation bzw. Quellenwechsel. Der echte HACS-/Anwenderversuch ist noch keine abgeschlossene Release-Abnahme. |
| [docs-removal-instructions](https://contributors.home-assistant.io/core/quality-scale/docs-removal-instructions/) | Belegt | `USAGE.md`, Abschnitt zur Entfernung: Eintrag, Entitäten, HACS-Komponente, abhängige Dashboards/Automationen; historische Statistiken werden nicht zur Löschung aufgefordert. |
| [docs-triggers](https://contributors.home-assistant.io/core/quality-scale/docs-triggers/) | Ausnahme | Keine eigenen Integrations-/Gerätetrigger. Normale Zustands-/Zahlentrigger sind in `USAGE.md` erklärt. |
| [entity-event-setup](https://contributors.home-assistant.io/core/quality-scale/entity-event-setup/) | Belegt | `CoordinatorEntity` verwaltet seine Listener. Der zusätzliche Forecast-Listener in `weather.py` wird beim Hinzufügen abonniert und mit `async_on_remove` abgebaut. Lifecycle-/WebSocket-Tests prüfen laufende Aktualisierung und Abbau. |
| [entity-unique-id](https://contributors.home-assistant.io/core/quality-scale/entity-unique-id/) | Belegt | Alle aktiven Entity-Familien haben Entry-basierte bzw. bewusst geteilte Diagnose-IDs. `test_complete_entry_setup_reload_and_unload` und registrierte Warnungs-/Messwerttests prüfen erhaltene Zuordnungen. |
| [has-entity-name](https://contributors.home-assistant.io/core/quality-scale/has-entity-name/) | Belegt | Alle neun aktiven Entity-Klassen in `sensor.py`, `weather.py`, `binary_sensor.py`, `pollen_sensor.py` setzen `_attr_has_entity_name = True`. |
| [runtime-data](https://contributors.home-assistant.io/core/quality-scale/runtime-data/) | Belegt | Typisierter `MeteoSwissConfigEntry` und `MeteoSwissRuntimeData` in `runtime_data.py`; nur gemeinsam benötigte Diagnose-Eigentümerschaft bleibt domainweit. |
| [test-before-configure](https://contributors.home-assistant.io/core/quality-scale/test-before-configure/) | Belegt | Beide Quellen prüfen vor dem Speichern den echten Beobachtungs-Coordinator mit 30 Sekunden Gesamttimeout. Fehler bleiben korrigierbar; Tests prüfen Fehler, Erfolg, Timeout und Abbruch. |
| [test-before-setup](https://contributors.home-assistant.io/core/quality-scale/test-before-setup/) | Belegt | `async_config_entry_first_refresh()` vor dem Plattformaufbau ermöglicht HA-Retry. Optionale Datenfamilien blockieren valide Beobachtungen nicht. `test_initial_failure_does_not_close_ha_session_or_leave_entry_data` prüft den Fehlerpfad. |
| [unique-config-entry](https://contributors.home-assistant.io/core/quality-scale/unique-config-entry/) | Belegt | Quellen-/Stations-/Koordinaten-/Warn-PLZ-Abgleich plus HA-Unique-ID; Alt-Einträge ohne Unique-ID werden ebenfalls erkannt. Duplikattests laufen vor unnötigen Netzabrufen. |

## Silver: alle zehn Regeln

| Regel | Bewertung | Konkreter Nachweis und Restarbeit |
|---|---|---|
| [action-exceptions](https://contributors.home-assistant.io/core/quality-scale/action-exceptions/) | Ausnahme | Keine eigenen Integrationsaktionen; bei späterer Einführung neu bewerten. |
| [config-entry-unloading](https://contributors.home-assistant.io/core/quality-scale/config-entry-unloading/) | Belegt | `__init__.py` nutzt HA-Plattformabbau, verwaltete Hintergrundtasks/Listener und die HA-eigene Session. `tests/test_reliability.py` prüft beide Quellen mit echtem Recorder, Reload, stabile IDs und vollständig entfernte Polling-Listener. `tests/test_startup.py` prüft Cancellation aller optionalen Kinderabrufe. |
| [docs-configuration-parameters](https://contributors.home-assistant.io/core/quality-scale/docs-configuration-parameters/) | Belegt | `USAGE.md` dokumentiert Intervall und separat gewählte Pollenmessstation samt Wirkung und Configure-Einstieg. Neue Dialoghilfen bleiben unabhängig davon eine Bronze-Lücke. |
| [docs-installation-parameters](https://contributors.home-assistant.io/core/quality-scale/docs-installation-parameters/) | Belegt | `USAGE.md` erklärt Quelle, Messstation, Warn-PLZ, Koordinaten, Intervall, Grenzen und das aktuelle Prognoseziel. Die PLZ ist bei Stations-Einträgen ausdrücklich nicht automatisch der Prognoseort. |
| [entity-unavailable](https://contributors.home-assistant.io/core/quality-scale/entity-unavailable/) | Teilweise/offen | Ausfall/Erholung der Hauptquellen ist über registrierte Entities belegt. Optionales UV liefert bei HTTP-/Timeout-/JSON-Fehlern ebenso `None` wie bei fehlendem Wert; die Entity erbt weiter den erfolgreichen AQ-Coordinator. UV-Ausfall daher künftig getrennt von einem unbekannten Einzelwert behandeln. Auch die Diagnose-Semantik eines gecachten Stationskatalogs explizit festhalten. |
| [integration-owner](https://contributors.home-assistant.io/core/quality-scale/integration-owner/) | Belegt | `@martins-netizen` ist Codeowner im Manifest und aktiv im Fork. Öffentliche Issues, Issue-Formulare und vertraulicher Meldeweg wurden am 17.10.2026 bestätigt. |
| [log-when-unavailable](https://contributors.home-assistant.io/core/quality-scale/log-when-unavailable/) | Teilweise/offen | Coordinator-Übergangslogs und private Fehlerketten sind für Beobachtungen, Warnungen, Prognose, Pollen/AQ und Messpollen getestet. Der separate UV-Abruf protokolliert Fehler nur auf Debug-Stufe und hat keinen eigenen Ausfall-/Erholungsübergang. Gemeinsam mit UV-Verfügbarkeit schliessen, ohne Koordinaten oder rohe URLs zu protokollieren. |
| [parallel-updates](https://contributors.home-assistant.io/core/quality-scale/parallel-updates/) | Belegt | `sensor.py`: 1 für pollende Diagnosen; `weather.py`, `binary_sensor.py`, `pollen_sensor.py`: 0 bei zentralen Coordinator-Abrufen. 0 bedeutet kein Entity-Semaphorlimit, nicht null Netzabrufe. Keine eigenen Geräteaktionen. |
| [reauthentication-flow](https://contributors.home-assistant.io/core/quality-scale/reauthentication-flow/) | Ausnahme | Die verwendeten öffentlichen Quellen benötigen keine Konten oder Anmeldedaten. |
| [test-coverage](https://contributors.home-assistant.io/core/quality-scale/test-coverage/) | Offen | Der gemessene Gesamtwert ist 99,0517 %, aber die Regel fordert mehr als 95 % je Modul. `camera.py`, `hydro.py`, `slf.py`, `version.py` stehen auf 0 %. Keine Ausnahme oder Ausblendung allein wegen des Gesamtwertes. |

## Prüfbasis und ihre Grenzen

Die sieben PR-Prüfungen von [PR #25](https://github.com/martins-netizen/ha-meteoswiss/pull/25)
waren erfolgreich. Nach dem regulären Squash-Merge auf `6d74354` sind auch
[CI](https://github.com/martins-netizen/ha-meteoswiss/actions/runs/39043774226),
[CodeQL](https://github.com/martins-netizen/ha-meteoswiss/actions/runs/39043774225)
und [HACS](https://github.com/martins-netizen/ha-meteoswiss/actions/runs/39043774217)
erfolgreich. Die Tests laufen auf HA 2026.8.3 und 2026.10.1.

Der zusätzliche bereits vorhandene Lauf auf HA 2026.10.2 mit offiziellen
Abhängigkeitsvorgaben bestand **762 Tests**. Dessen JSON-Coverage wurde erneut
ausgewertet: 2379/2408 Statements und 650/650 Zweige, kombiniert 99,0516678 %.
Nur `const.py` (98,5075 %) sowie die vier oben genannten Module liegen unter
100 %. Diese Prüfung hat für Dokumentationsänderungen keinen neuen identischen
Gesamttestlauf gestartet. Codegleichheit und vorhandene Läufe sind ausdrücklich
die Grundlage, keine neue Live-Abnahme.

Wichtige konkrete Regressionen liegen in
[`test_config_flow.py`](../tests/test_config_flow.py),
[`test_reliability.py`](../tests/test_reliability.py),
[`test_entity_warning_contracts.py`](../tests/test_entity_warning_contracts.py),
[`test_weather_entity.py`](../tests/test_weather_entity.py),
[`test_pollen_sources.py`](../tests/test_pollen_sources.py),
[`test_precipitation_sources.py`](../tests/test_precipitation_sources.py) und
[`test_station_logging.py`](../tests/test_station_logging.py).
Sie prüfen unter anderem Erholung, Registry-/Statistikidentität, Recorder-Upserts,
HA-Session-Eigentum, Listenerabbau und private Fehlerausgaben.

### Zuordnung des UV-Befunds zur installierten Version

Auch die UV-Lücke besteht bereits in **V1.5 / `567a5e4`**. Ein direkter
Git-Vergleich von `pollen_coordinator_openmeteo.py` und `sensor.py` mit `6d74354`
zeigt keine Unterschiede. Sie wird jetzt erkannt, wurde aber nicht durch einen
neueren Kandidaten eingeführt. Gemeint ist der hypothetische Fehler-/Statuspfad:
Ein aktuell vorhandener UV-Wert ist dadurch nicht als falsch bewertet.
Bei einem separaten UV-Abruffehler erscheint bislang `unknown` statt einer
eigenständig belegten Nichtverfügbarkeit, während gesunde AQ-Daten bleiben.

## Gezielte nächste Umsetzung nach R0

1. **Dialog und Abrufperiode:** `data_description` für jeden tatsächlich
   sichtbaren Parameter in DE/EN/FR/IT ergänzen. Quellenwahl, Messstation,
   Warn-PLZ und Prognosekoordinaten direkt erklären. Das Intervall aus der
   normalen Einrichtung/Optionen nehmen; Umgang mit vorhandenen abweichenden
   Werten samt Migration vorher festlegen. Keine still geänderte Abruflast.
2. **UV-Quellenzustand:** Erfolgreichen Abruf ohne Einzelwert, Transport-/Payload-
   ausfall und Erholung unterscheiden. Nur UV als ausgefallen markieren;
   gesunde AQ-/Pollenwerte behalten. Einmalige private Übergangslogs sowie
   registrierte Entity-Tests für diese drei Fälle ergänzen.
3. **Module und Abdeckung:** Referenzen der inaktiven Radar-/Hydro-/SLF-Dateien
   prüfen und ihren ausgelieferten Umfang bewusst entscheiden. Allgemeine
   historische Kommentare über fehlende öffentliche APIs nicht ungeprüft als
   aktuelle Aussage übernehmen. Bestehende Hochwasser-/Lawinenwarnungen im
   gemeinsamen Warnungsclient bleiben davon unabhängig. Versionskonsistenz
   beibehalten; keine bedeutungslosen Importtests nur für eine Zahl.
4. **Gemeinsame Entity-/Coordinator-Struktur:** Die Wiederholung von Geräteinfo,
   Attribution und Basiseigenschaften untersuchen; einen kleinen passenden
   gemeinsamen Baustein einführen. Quellenadapter nicht pauschal vereinigen.
5. **Externer Brand-Nachweis:** Custom-/HACS-Darstellung und Core-Regel bewusst
   getrennt dokumentieren; dafür keine offizielle Stufe vortäuschen.

Jeder Laufzeit-PR erhält gezielte Tests und die bestehenden Pflichtprüfungen.
Zunächst wird die laufende Freigabe R0 abgeschlossen. Reihenfolge und
Bestandsschutz stehen im [freigegebenen Plan](NEXT_RELEASE_PLAN_DE.md).

## Ergänzender UX-Befund aus der Sichtprüfung

Das Bildschirmfoto vom 17.10.2026 zeigt auf der Warnungs-Geräteseite
«Sicher/Unsicher». Ursache ist `BinarySensorDeviceClass.SAFETY` bei allen drei
Warnsensoren. Ein inaktiver Warnsensor belegt keine allgemeine Sicherheit.
Das ist ein Darstellungsbefund; die boolesche Warnungslogik wird dadurch nicht
als falsch bewertet.

| Sensor | Anzeige bei `off` | Anzeige bei `on` |
|---|---|---|
| Wetterwarnung | Keine aktive Warnung | Warnung aktiv |
| Kritische Wetterwarnung | Keine kritische Warnung | Kritische Warnung aktiv |
| Angekündigte Wetterwarnung | Keine angekündigte Warnung | Warnung angekündigt |

Dies sind Zieltexte für einen getrennten Übersetzungs-/UX-PR nach R0.
Die vorhandenen `translation_key`s erlauben integrationsbezogene Zustandsnamen;
der aktuelle HA-Frontend-Code priorisiert sie vor der Geräteklasse. Umsetzung
und Verhalten auf beiden unterstützten HA-Versionen noch gezielt prüfen.
`on`/`off`, Schwellen, IDs und Automationen bleiben erhalten. `unknown` und
`unavailable` werden nicht in «keine Warnung» umgedeutet. Alle vier Sprachen
mitliefern; die tatsächliche Standard-Geräteseite zusätzlich visuell abnehmen.

Quellen: [HA-Binärsensorzustände](https://www.home-assistant.io/integrations/binary_sensor/),
[Frontend-Zustandsanzeige](https://github.com/home-assistant/frontend/blob/dev/src/common/entity/compute_state_display.ts).
Gold-Regeln zu Übersetzungen/Geräteklassen werden danach gesondert bewertet.

### Pollen-Sichtbefund und aktueller Quellenvergleich

Auch das zweite Bildschirmfoto gehört laut Benutzer zum installierten **V1.5**.
`binary_sensor.py`, `sensor.py` und `pollen_meteoswiss.py` sind zwischen V1.5
(`567a5e4`) und der Prüfbasis `6d74354` bytegleich. Die Befunde werden deshalb
nicht als Beobachtungen eines bereits installierten V1.7 ausgegeben.

- **Hasel-Icon:** `sensor.py` setzt `mdi:branch`. Im offiziellen
  [MaterialDesign-Katalog](https://github.com/Templarian/MaterialDesign/tree/master/svg)
  fehlt `branch.svg` (404); `tree-outline.svg` ist vorhanden. Ein gültiges
  Baum-/Blattsymbol wählen und im getrennten UX-PR mitsamt realer Anzeige prüfen.
- **Tatsächlicher Messumfang:** Der aktuelle Zürcher Datensatz PZH und das
  offizielle Parameterverzeichnis liefern sieben stündliche Pollenarten:
  Erle, Birke, Hasel, Buche, Esche, **Eiche**, Gräser. Der Fork liest nur sechs.
  Eiche ist damit eine belegte Erweiterung für einen eigenen Daten-/Entity-PR.
  Der vorhandene, ungenutzte `POLLEN_PARAM_MAP` führt zudem `kaqueth0`; der
  tatsächlich dokumentierte und gelieferte Eichenparameter heisst `kaquerh0`.
- **Ambrosia und Beifuss:** Weder das aktuelle PZH-Stunden-CSV noch das gelesene
  OGD-Parameterverzeichnis enthält diese beiden Arten. Vorhandene
  Open-Meteo-Entities sind modellierte Werte, keine MeteoSchweiz-Stationsmessung.
  Der MeteoSchweiz-Klimareport 2024 beschreibt separate manuelle Ambrosiamessungen
  und die damalige fehlende automatische Bestimmung beider Arten; daraus wird
  kein unbestätigter heutiger Echtzeit-Messdienst abgeleitet.
- **Nachfolgender Gold-Review:** Die Gruppierung der fachlichen Messwerte als
  Diagnose und die bisherige Einheit nur als Attribut sind bewusst erhaltene
  Altverträge. Deren bessere Darstellung separat prüfen; keine unbemerkte
  Unit-/Statistik-/Registry-Migration als Teil eines Icon-Fixes.

Nachweis: [kompakte Quellenprüfung](evidence/pollen_source_2026-10-17.json),
[aktuelles PZH-CSV](https://data.geo.admin.ch/ch.meteoschweiz.ogd-pollen/pzh/ogd-pollen_pzh_h_now.csv),
[Parameterverzeichnis](https://data.geo.admin.ch/ch.meteoschweiz.ogd-pollen/ogd-pollen_meta_parameters.csv),
[Dateninventar](https://data.geo.admin.ch/ch.meteoschweiz.ogd-pollen/ogd-pollen_meta_datainventory.csv),
[Klimareport 2024](https://www.meteoschweiz.admin.ch/dam/jcr%3Afd79265c-bd1c-4229-ae8d-ea69184d94b8/Klimareport-2024-de.pdf).
