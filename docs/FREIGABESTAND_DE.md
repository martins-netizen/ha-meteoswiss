# Freigabestand: Beta und erste stabile Version

**Dokumentversion:** 1.0 · **Stand:** 20. Oktober 2026
**Zweck:** Aktueller Einstieg in erledigte Nachweise, verbleibende Release-
Schritte und ausdrücklich spätere Entwicklung.

## Bereits abgeschlossen

| Nachweis | Bestätigter Stand |
|---|---|
| Erste öffentliche Beta | `8.2.0b1`, am 20.10.2026 um 17:56:24 MESZ veröffentlicht; unveränderlicher Tag auf `abbb6b7701134ac2573f35b425ab3f0697a80540`. Es ist ein Community-Fork, kein offizielles MeteoSchweiz-Produkt. |
| Technische Laufzeitabnahme | HA 2026.10.2, akzeptierter Quellstand `0086b956d44b7144b242c5d5c1881d0b0650e524`, eigene 24-Stunden-Beobachtung und Sichtprüfung abgeschlossen. Die 33 veröffentlichten Komponenten-/Sprach-/Brand-Dateien entsprechen diesem Stand. |
| Tests und Qualität des Kandidaten | 786 Tests je HA 2026.8.3/2026.10.2, 99,051 % kombinierte Zeilen-/Zweigabdeckung; erfolgreiche Kandidatenprüfungen einschliesslich HACS, Hassfest und CodeQL. Das ist keine vollständige Silver-Einstufung. |
| HACS-Quellenwechsel | Betreiber bestätigt am 20.10.2026 HACS 2.0.5, `martins-netizen/ha-meteoswiss`, heruntergeladene `8.2.0b1`, Neustart und positive erste Sichtprüfung. |
| Warnungen, Sprachen und Migration | App v3 mit verifiziertem Katalog; DE/EN/FR/IT gebündelt; tatsächlich betroffene Verbraucher, erhaltene Identitäten und Regenstatistik bei der technischen Laufzeitabnahme geprüft. |
| Optionaler UV-Ausfall | Ein isolierter Ausfall am 19.10.2026 erholte sich beim nächsten regulären Abruf. Andere geprüfte Datenfamilien blieben verfügbar. |

Die [HACS-Abnahme](HACS_ABNAHME_DE.md) beschreibt die Beleggrenzen.
Die letzte Betreiberbestätigung ersetzt keine neu erhobenen Live-Prüfsummen,
Registry-/Statistikvergleiche nach dem HACS-Wechsel oder einen ausgeführten
Rollback. Der bereits dokumentierte Wechsel wird dennoch als abgeschlossen
geführt und nicht ohne konkreten Anlass wiederholt.

## Noch vor der ersten stabilen Version

Die Zielbezeichnung **8.2.0** beschreibt die erste stabile Fork-Version;
sie ist noch nicht veröffentlicht oder automatisch freigegeben.

| Reihenfolge | Arbeit | Fertig, wenn … |
|---|---|---|
| 1 | **Leere HACS-Erstinstallation praktisch prüfen** | In einer temporären isolierten HA-Instanz: Custom Repository hinzufügen, Beta explizit auswählen und herunterladen, neu starten, Einrichtungsdialog einmal durchlaufen, erste Daten und verständliche Fehler prüfen. Die deutsche Einstiegsanleitung wird dabei Schritt für Schritt abgearbeitet. |
| 2 | **Rückweg im isolierten Test durchlaufen** | Gesicherte Software/Konfiguration lassen sich nach dem dokumentierten Verfahren wiederherstellen; betroffene Warnungsfilter gehören zum gemeinsamen Rückweg. Kein Test an produktiven Geräten. Vorhandene simulierte Werkzeugtests und ein beschriebener Rückweg werden nicht als tatsächlich ausgeführter Rollback ausgegeben. |
| 3 | **Restbefunde und Freigabeumfang abschliessen** | Ergebnisse aus Neuinstallation, Anleitung und Qualitätsreview sind bewertet. Releaseverhindernde Fehler sind behoben und passend getestet; verbleibende begründete Einschränkungen sind für Nutzer sichtbar. Ein vollständiger Silver-/Gold-Abschluss ist keine Voraussetzung. |
| 4 | **Stabilen Versionsstand vorbereiten** | Manifest und Modulversion passen zu 8.2.0; Release-/Wechselhinweise sind aktuell. `hide_default_branch: true` wird im nächsten geprüften HACS-Manifest mitgeliefert und sein Versionsauswahlverhalten geprüft. Der vorhandene unveränderliche Beta-Tag wird nicht verschoben. |
| 5 | **Exakten Kandidaten prüfen und regulär freigeben** | PR-Prüfungen und passende HA-Kompatibilitätsläufe sind grün, Diff zum abgenommenen Runtime-Stand geprüft, regulärer Merge erfolgt und der Veröffentlichungsentscheid bezieht sich auf genau diesen Commit. |
| 6 | **Stabil veröffentlichen und HACS-Angebot kontrollieren** | Separater stabiler Tag/Release ist angelegt, Version und Paketinhalt stimmen, HACS bietet die stabile Version korrekt an. Erst dann gilt die stabile Veröffentlichung als erfolgt. |

Für die Erstinstallation muss der Anwender **keine zweite dauerhafte HA-
Umgebung bereitstellen und seine produktive Integration nicht löschen**.
Die temporäre Prüfung bleibt offen, bis sie tatsächlich ausgeführt wurde.

Ein neuer unabhängiger **rein lesender** Vergleich von installierten Dateien,
Identitäten und Statistikfortschritt nach dem HACS-Wechsel ist als ergänzender
Nachweis sinnvoll. Er wurde noch nicht erhoben und verlangt weder erneuten
Quellenwechsel noch Löschung, Neustart oder eine neue 24-Stunden-Frist.

Reine Dokumentationsänderungen erfordern keine HA-Aktualisierung. Auch eine
reine Versions-/Verpackungsänderung setzt die bereits abgeschlossene
Betriebsabnahme nicht automatisch zurück. Bei fachlichen Laufzeitänderungen
werden dagegen der betroffene Test- und Beobachtungsumfang vorab festgelegt.
Neue Features werden nicht in einen abgenommenen Kandidaten eingeschoben.

## Sicherheits- und Qualitätsrestpunkte richtig einordnen

Der [Review vom 17.10.2026](REVIEW_2026-10-17.md) nennt zwei Härtungsaufträge:
gemeinsame Ziel-/Weiterleitungs-/Grössenprüfung der Quellenzugriffe sowie eine
sichere CodeQL-Prüfroute für Beiträge aus fremden Forks. Ihre Erledigung ist hier
nicht belegt. Die Quellenhärtung wird vor dem stabilen Freigabeentscheid nochmals
nach Risiko bewertet; eine konkret ausnutzbare Schwachstelle war im damaligen
Review nicht nachgewiesen. Vor der Annahme externer Fork-Beiträge muss deren
sichere Analyse tatsächlich gewährleistet sein.

Weitere Bronze-/Silver-Restpunkte betreffen insbesondere Intervall-/Feldkonzept,
gemeinsames Modul-Layout, Core-Brand-Nachweis und inaktive Platzhalter beziehungsweise
deren Einzelabdeckung. Sie bleiben in der [Qualitätsmatrix](QUALITY_SCALE.md)
sichtbar. Hohe Gesamtcoverage, HACS-Validierung oder ein erfolgreicher Betrieb
schliessen diese Punkte nicht pauschal. Ein unabhängiger Verständlichkeitstest
mit einem neuen nichttechnischen Anwender wurde ebenfalls nicht durchgeführt;
der eigene Erstinstallationsdurchlauf ersetzt eine solche Fremdbeurteilung nicht.

## Spätere Entwicklung, ohne die stabile Version aufzublähen

- **Orts-/POI-Auswahl und direkte Lokalprognosen:** Der offizielle OGD-
  Punktekatalog wird vorrangig untersucht. Katalogauswahl und Prognosequelle
  bleiben getrennte Entscheidungen; die vorgeschlagene Planung steht in
  [PR #35](https://github.com/martins-netizen/ha-meteoswiss/pull/35).
- **Warnschnittstelle:** Die bestehende MeteoSchweiz-App-API v3 bleibt bis auf
  Weiteres bestehen. Eine Ablösung durch MeteoGate/MeteoAlarm gehört nicht zum
  aktuellen Auftrag.
- **Silver und später Gold:** Nachweise regelweise abschliessen; keine offizielle
  HA-Qualitätsstufe oder HACS-Zertifizierung behaupten.
- **HACS-Standardkatalog:** Eigene spätere Einreichung mit dann aktuellen Regeln
  und passendem `country`-Eintrag im veröffentlichten Manifest. Die Nutzung als
  Custom Repository und eine stabile GitHub-Version sind davon unabhängig.

## Nachweisorte

- [Veröffentlichungsablauf und genaue Quellen](PUBLISHING.md)
- [HACS-Abnahme mit Betreiberbestätigung und Beleggrenzen](HACS_ABNAHME_DE.md)
- [Beta-Umfang und aktuelle Einschränkungen](RELEASE_8.2.0b1.md)
- [Qualitätsmatrix und verbleibende Kriterien](QUALITY_SCALE.md)
