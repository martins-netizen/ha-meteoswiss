# Zu diesem gepflegten Fork wechseln

Diese Anleitung gilt, wenn bereits eine MeteoSwiss-Integration vorhanden ist.
Der Fork ersetzt ihre Software. Die bestehende Einrichtung in Home Assistant
wird weiterverwendet: **MeteoSwiss unter Geräte & Dienste nicht löschen und
nach dem Wechsel nicht nochmals hinzufügen.**

Prüfe zuerst den [Veröffentlichungsstatus](../README.md#release-status).
Ohne ausdrücklich freigegebene Version ist diese Anleitung noch keine
Installationsfreigabe. Ein Branch oder ein offener Pull Request ist keine Release-Version.

## 1. Deinen Ausgangspunkt feststellen

| Bereits vorhandene Installation | Vorgehen |
|---|---|
| Derselbe gepflegte Fork, bereits über HACS | Nach Prüfung der Release-Hinweise nur die freigegebene Version herunterladen; keinen zweiten Repository-Eintrag anlegen |
| `LNKtwo/ha-meteoswiss` über HACS | Die unten beschriebene Umstellung des HACS-Softwareeintrags verwenden |
| Manuell kopierte Dateien, lokale Änderungen oder unbekannte Herkunft | Zuerst Herkunft und Änderungen klären; nicht einfach überschreiben |

Öffne dazu den MeteoSwiss-Eintrag in **HACS → Dreipunktmenü → Repository**.
Notiere Repository und Versionsnummer. Eine gleiche Versionsnummer beweist
bei manuell geänderten Dateien nicht, dass derselbe Code installiert ist.
Wenn du das nicht sicher zuordnen kannst, halte hier an und frage im
[Fork-Issue-Tracker](https://github.com/martins-netizen/ha-meteoswiss/issues) nach.

## 2. Backup und bestehende Verwendung prüfen

Erstelle unter **Einstellungen → System → Backups** ein vollständiges
Home-Assistant-Backup, lade es herunter und bewahre
den Wiederherstellungsschlüssel auf. Es muss die bisherige Integration sowie
Einrichtung, Dashboards und Automationen abdecken. Behalte auch die bisherige
Softwareversion für den Rückweg. Bei einer externen Datenbank muss auch deren
Sicherung dazugehören. Ein ungetestetes Backup ist kein nachgewiesener Restore.

Notiere die wichtigsten bisherigen Entitäten und vorhandenen Statistikdiagramme.
Die Kennungen regulär weitergeführter Entitäten und der Niederschlagsstatistik
sollen nach dem Wechsel gleich bleiben. Zwei Grenzen sind vorab wichtig:

- Ein alter, nur aus Prognosen abgeleiteter **Saison-Heizgradtage-Sensor** wird
  bewusst entfernt. Er war kein verlässlicher aufaddierter Messzähler.
  Verweise darauf müssen angepasst werden; der tägliche HGT-12/20-Sensor bleibt
  eine Prognose. Ein neuer gemessener Saisonzähler wird nicht angelegt.
- Bodentemperatur-Sensoren und eigenständige Radar-/SLF-/BAFU-Module sind im
  aktuellen Fork nicht als aktive Funktionen enthalten. Plane ihre Nutzung
  nicht auf Grundlage älterer Upstream-Ankündigungen.

## 3. Besonders wichtig: Wetterwarnungen in Automationen

Die bisherige Warnartenzuordnung war teilweise falsch. Eine Softwareaktualisierung
korrigiert **nicht automatisch** deine eigenen Dashboards oder Automationen.

| Gemeinte Warnung | Jetzt bestätigte Nummer |
|---|---:|
| Wind / Sturm | **0** |
| Gewitter | **1** |
| Regen / Starkregen | **2** |
| Schnee / Schneefall | **3** |
| Strassenglätte | **4** |
| Frost, mit konkretem Ereignistext | **5** |
| Tauwetter, falls vom Anbieter ausgegeben | **6** |
| Trockenheit | **12** |

Die [vollständige Zuordnung](WARNING_CODES.md#numeric-warning-families) umfasst
13 Warnarten. Nummer 4 darf nicht mehr als Wind interpretiert werden.
Ein Filter für **Wind, Gewitter und Regen** verwendet nun **`[0, 1, 2]`**
anstelle des alten **`[1, 2, 4]`**. Ersetze deshalb nicht jede Zahl 4 in der Konfiguration.

Nutzt du Warnungen zur Steuerung von Markisen, Storen oder anderen Geräten:

1. Notiere, welche betroffenen Automationen eingeschaltet sind, und pausiere
   sie für die Umstellung.
2. Prüfe aktive **und angekündigte** Warnungen, Vorlaufprüfungen sowie Beschriftungen.
   Ein alter fester Text „Bodenfrost“ passt nicht zu jedem Ereignis der Kategorie Frost.
3. Passe die betroffenen Verweise zusammen mit der neuen Software an und prüfe
   das Ergebnis, bevor du die zuvor eingeschalteten Automationen wieder aktivierst.

Wenn du nicht weisst, ob solche Zahlen in deiner Konfiguration verwendet
werden, lass diesen Teil zuerst prüfen. Die richtige Reaktion auf einen
Warnungsausfall hängt von deiner Anlage ab; **Nicht verfügbar** ist keine
Freigabe zum Öffnen einer Markise. Starte zur Prüfung keine Geräteaktion.

## 4. Softwareeintrag in HACS umstellen

Für einen Wechsel von `LNKtwo/ha-meteoswiss`:

1. Entferne in **HACS** über das Dreipunktmenü den alten Repository-Eintrag.
   Das entfernt die dort verwalteten Softwaredateien. Es ist **nicht** das
   Löschen der eingerichteten Integration unter **Geräte & Dienste**.
2. Füge in **HACS → Dreipunktmenü → Benutzerdefinierte Repositories**
   `https://github.com/martins-netizen/ha-meteoswiss` als **Integration** hinzu.
3. Öffne **MeteoSwiss (maintained fork)** und lade die ausdrücklich freigegebene
   Version herunter. Bei Vorabversionen muss deren Anzeige gegebenenfalls
   erst aktiviert werden. Wenn die Zielversion fehlt oder HACS die Umstellung
   ablehnt, halte an; weder die HA-Einrichtung löschen noch versteckte
   Konfigurationsdateien bearbeiten.
4. Prüfe die gleichzeitig vorbereiteten Warnungsanpassungen und starte
   Home Assistant anschliessend **einmal neu**. Zwischen Entfernen und Ersetzen
   der Software ist kein zusätzlicher Neustart vorgesehen.

Beide Repositories verwalten denselben Integrationsordner `meteoswiss`.
Sie sollen nicht gleichzeitig als aktive Softwarequellen geführt werden.
Ein HACS-Wechsel löscht absichtlich keine Messhistorie, ersetzt aber die alten
Komponentendateien: lokale Code- oder Übersetzungspatches müssen vorher geklärt sein.

## 5. Ergebnis prüfen

- Die **bestehende** Integration lädt mit der bisherigen Station und Postleitzahl.
- Weiterverwendete Entitäten haben dieselben Kennungen; bestehende Diagramme
  und die offizielle stündliche Niederschlagsstatistik sind weiterhin vorhanden.
- Messwerte, Prognose sowie aktive und angekündigte Warnungen sind plausibel.
  Die erfolgreiche Meldung „keine Warnung“ ist von einem Quellenausfall unterscheidbar.
- Pollenmessstation, gewünschte deaktivierte Hilfssensoren und persönliche
  Anzeigepräzisionen sind erhalten. Wetterstation und Pollenmessstation sind unabhängig.
- Eigene Warnungskarten und Automationen verwenden die neue Zuordnung.
  Aktiviere danach nur diejenigen betroffenen Automationen wieder, die zuvor aktiv waren.

Fehlende Einzelwerte sind nicht automatisch Installationsfehler. Siehe
[Werte und Datenlücken](START_DE.md#4-pollenmessstation-und-erste-werte-prüfen).
Eine erfolgreiche Sichtprüfung ersetzt keine Beobachtung im normalen Betrieb.
Die Prüfung eines älteren Code-Stands gilt nicht automatisch für einen neueren.

## Wenn etwas nicht funktioniert

Pausiere weiterhin die betroffenen Geräteautomationen. Nutze das geprüfte
Backup bzw. den vorbereiteten Rückweg, um **Software und zusammengehörige
Warnungsanpassungen** auf den alten Stand zurückzusetzen. Danach Home Assistant
neu starten und den alten Stand prüfen. Code und Warnungsfilter unterschiedlicher
Generationen dürfen nicht vermischt werden.

Lösche keine Einträge, Entitäten oder Statistikdaten, um einen Fehler zu
„beheben“. Für Hilfe genügen zunächst Version, Ausgangsrepository, Zeitpunkt
und relevante geschwärzte Meldungen. Poste keine vollständigen Backups oder Zugangsdaten.

Die vier mitgelieferten Sprachen werden mit der Software aktualisiert.
Kopiere keine alten Übersetzungsdateien darüber. Eigene Dashboard-Texte sind
dagegen Teil deines Dashboards und werden gesondert gepflegt.
