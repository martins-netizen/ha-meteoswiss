# HACS-Abnahme der ersten Beta

**Stand: 20. Oktober 2026 · Plan V1.0**

Die Beta **8.2.0b1** ist veröffentlicht. Ihr Integrationscode entspricht dem
bereits auf HA 2026.10.2 abgenommenen Stand. Offen ist der konkrete Weg über
HACS: zuerst die Versionsauswahl, danach Erstinstallation und Quellenwechsel.
Dafür muss der bestehende HA-Betriebstest nicht nochmals beginnen.

## 1. Zuerst nur nachsehen

Auf dem vorhandenen System wird in diesem Schritt keine Software entfernt oder
heruntergeladen und Home Assistant nicht neu gestartet.

1. Öffne **HACS** und suche nach **MeteoSwiss**.
2. Öffne beim vorhandenen Eintrag **Dreipunktmenü → Repository**. Notiere die
   angezeigte GitHub-Adresse und die in HACS geführte installierte Version.
   Notiere auch die installierte HACS-Version. Ein nicht vorhandener Eintrag
   ist ebenfalls ein Ergebnis; die HA-Integration deshalb nicht löschen.
3. Zeigt der Softwareeintrag bereits auf **martins-netizen/ha-meteoswiss**,
   wähle **Informationen aktualisieren / Update information**.
   Das aktualisiert Metadaten, ohne Integrationsdateien herunterzuladen.
4. Öffne bei diesem Fork **Herunterladen / Download** beziehungsweise
   **Erneut herunterladen / Redownload**. Klappe **Andere Version benötigt? /
   Need a different version?** auf und suche im Feld **Release** nach
   **8.2.0b1**. Wähle sie zur Kontrolle und prüfe, welche Version der Dialog
   ankündigt. **Danach Abbrechen / Cancel**, nicht den Download bestätigen.
   Ältere HACS-Versionen können zusätzlich eine Beta-Anzeigeoption haben.
5. Zeigt der vorhandene Softwareeintrag auf **LNKtwo/ha-meteoswiss**, entferne
   ihn für diese Vorprüfung noch nicht. Erst Herkunft, Backup und Rückweg
   bestätigen; die spätere Umstellung folgt [WECHSEL_DE.md](WECHSEL_DE.md).
   Ein zusätzlicher Eintrag darf nicht ungeprüft denselben installierten
   Ordner übernehmen.

Für diese Vorprüfung genügen HACS-Version, Repository-Adresse, dort angezeigte
Version und die angebotene Zielversion. Screenshots dürfen diese Felder zeigen,
brauchen aber keine Geräte-, Benutzer- oder Zugangsdaten zu enthalten.
Die auf GitHub vorhandene Beta beweist noch nicht ihre Anzeige im lokalen HACS.

## 2. Zwei getrennte praktische Prüfungen

| Prüfung | Geeignete Umgebung | Was tatsächlich belegt werden muss |
|---|---|---|
| Neuinstallation | Temporäre leere HA-Instanz mit HACS, ohne produktive Gerätesteuerung | Custom Repository als Integration hinzufügen; ausdrücklich 8.2.0b1 herunterladen; neu starten; genau einmal MeteoSwiss einrichten; Stations-/Warnort und erste Werte prüfen |
| Quellenwechsel | Temporäre Instanz mit bestehender MeteoSwiss-Einrichtung oder separat geplanter produktiver Wechsel nach Vorprüfung und geprüftem Rückweg | Bisherige HACS-Softwarequelle ersetzen, vorhandenen HA-Eintrag erhalten; Zielversion/Dateien, weitergeführte IDs, Einstellungen und Statistiken vor/nach dem Wechsel vergleichen |

Eine zweite dauerhafte Testinstallation ist nicht nötig. Eine produktive
Instanz mit vorhandener Integration ist keine leere Erstinstallation.
Ein erfolgreicher Versionsdialog ist noch kein erfolgreicher Download.

### Neuinstallation

Folge [START_DE.md](START_DE.md) und notiere HA-/HACS-Version, Zeitpunkt,
Release-Auswahl, erfolgreiche Rückkehr nach Neustart sowie den Abschluss des
Einrichtungsdialogs. Prüfe Wetterstation, vierstellige Warnpostleitzahl,
HA-Standort für die Prognose und die unabhängig gewählte Pollenmessstation.
Messwerte, Prognose, Warnungen, Pollen und Luftqualität sollen nachvollziehbar
angelegt sein. Fehlende optionale Werte sind von Quellenausfällen zu unterscheiden.

### Quellenwechsel

Folge [WECHSEL_DE.md](WECHSEL_DE.md). Der Umfang hängt von der tatsächlichen
Ausgangsquelle ab. Der bereits mit dem Installer übernommene gepflegte Fork
enthält andere Warnungskorrekturen als eine ältere unveränderte Upstream-Version;
deren Migrationsaufgaben dürfen nicht pauschal erneut ausgeführt werden.

Vor der Umstellung: gesicherten Softwarestand und zugehörige Konfiguration
samt Wiederherstellungsweg bestätigen. Betroffene Warnungssteuerungen nur bei
einer tatsächlichen fachlichen Umstellung wie in der Wechselanleitung behandeln.
Keine Geräte nur zu Testzwecken auslösen. Nach dem Wechsel bleibt genau eine
aktive HACS-Softwarequelle für den Ordner `meteoswiss` bestehen. Den vorhandenen
Eintrag unter **Geräte & Dienste** weiterverwenden.

Vergleiche für weitergeführte Entitäten und Statistiken die tatsächlichen
Kennungen, Einstellungen und Daten. Für Kloten bleibt das amtliche
Stundenarchiv `meteoswiss:klo_precipitation_hourly` erhalten. Bewusst entfernte
Altentitäten sind in der Wechselanleitung genannt; keine Historienbereinigung.
Bei Problemen Software **und zugehörige Warnungsfilter** gemeinsam zurücksetzen.

## 3. Aktueller Nachweisstand

| Nachweis | Stand |
|---|---|
| Öffentlicher GitHub-Prerelease und aufgelöster Tag | Bestätigt: 8.2.0b1 → abbb6b7701134ac2573f35b425ab3f0697a80540 |
| Laufzeitcode auf HA 2026.10.2, 24 Stunden und Sichtprüfung | Abgeschlossen; Veröffentlichung enthält dieselben 33 Komponenten-/Sprach-/Brand-Dateien |
| HACS-Version und vorhandene Softwarequelle des konkreten Systems | Für diese HACS-Abnahme noch zu erfassen |
| 8.2.0b1 im tatsächlichen HACS-Dialog ausdrücklich auswählbar | Noch praktisch zu bestätigen |
| Leere HACS-Erstinstallation | Offen |
| HACS-Quellenwechsel mit Identitäts-/Statistikerhalt | Offen |
| Branch im Versionsangebot zuverlässig ausgeblendet | Für 8.2.0b1 nicht zugesichert; deren hacs.json enthält hide_default_branch nicht |
| HACS-Standardkatalog oder offizielle HA-Qualitätsstufe | Nicht beantragt beziehungsweise nicht bestätigt |

Die Prüfung der offiziellen HACS-Dokumentation und des aktuellen Quellcodes
klärt den vorgesehenen Bedienweg. Sie ersetzt keinen dieser offenen Praxistests.
Der veröffentlichte Beta-Tag bleibt unverändert; eine künftige Branch-Ausblendung
muss mit der passenden veröffentlichten Manifest-Version geprüft werden.

## Referenzen

- [HACS: eigenes Repository hinzufügen](https://www.hacs.xyz/docs/faq/custom_repositories/)
- [HACS: Metadaten aktualisieren und bestimmte Version herunterladen](https://www.hacs.xyz/docs/use/repositories/dashboard/)
- [HACS: Manifest und hide_default_branch](https://www.hacs.xyz/docs/publish/start/)
- [HACS: versionsabhängiges Lesen des Manifests](https://github.com/hacs/integration/blob/main/custom_components/hacs/repositories/base.py)
- [HACS: Release-Liste im Download-Dialog](https://github.com/hacs/frontend/blob/main/src/components/dialogs/hacs-download-dialog.ts)
