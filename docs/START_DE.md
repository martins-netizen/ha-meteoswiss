# MeteoSwiss neu einrichten

Diese Anleitung richtet sich an Anwender ohne Programmierkenntnisse.
Du brauchst weder ein MeteoSchweiz-Konto noch einen API-Schlüssel oder Terminalbefehle.
HACS muss bereits eingerichtet sein; der Weg dorthin ist unten verlinkt.

**MeteoSwiss ist bereits installiert?** Dann verwende stattdessen die
[Anleitung für den Wechsel](WECHSEL_DE.md). Die vorhandene Integration bleibt dabei erhalten.

## Was bringt mir dieser Fork?

Du möchtest Schweizer Wetterdaten direkt in deinem gewohnten Home-Assistant-
Dashboard sehen? Die Integration verbindet Messwerte, Prognosen, Warnungen,
Pollen und Luftqualität. Ein «Fork» ist eine weitergeführte Variante des
[ursprünglichen Projekts](https://github.com/LNKtwo/ha-meteoswiss).
Hier werden geprüfte Korrekturen und die vier Sprachen gemeinsam mitgeliefert.

| Dein Nutzen | Was du damit bekommst |
|---|---|
| Wetter am gewählten Ort verfolgen | Messwerte einer Schweizer Wetterstation, stündliche Niederschlagsstatistik und eine Modellprognose; die Station misst nicht direkt an deinem Haus |
| Naturgefahren im Blick behalten | Aktive und angekündigte Warnungen für deine Postleitzahl, mit Gefahrenstufe und Ereignistext; dazu können auch Hochwasserwarnungen des BAFU und Lawinenwarnungen des SLF gehören, wenn sie im Feed geliefert werden |
| Pollen und Luftqualität einbeziehen | Gemessene Pollen der gewählten Pollenstation sowie modellierte Pollen- und Luftqualitätswerte |
| Weniger von Hand nachpflegen | Deutsche, englische, französische und italienische Oberflächentexte kommen mit der Software; eine zusätzliche Wetterkarte ist nicht erforderlich |
| Fehlende Daten erkennen | Ein echter Nullwert, ein fehlender Einzelwert und eine ausgefallene Quelle werden unterschieden; eine ausgefallene Warnungsquelle gilt nicht als Entwarnung |

**Warum diese Variante wählen?** Sie bündelt nachvollziehbar geprüfte
Korrekturen, unter anderem bei Warnungszuordnung, Datenalter und
Niederschlagsstatistik. Änderungen, Tests und bekannte Grenzen sind öffentlich
dokumentiert; für Fragen gibt es einen eigenen
[Issue-Tracker](https://github.com/martins-netizen/ha-meteoswiss/issues).
Einzelne Funktionen können in anderen Versionen bereits vorhanden sein.

**Du kennst Home Assistant bereits gut?** Direkt zu
[Datenquellen und Einstellungen](USAGE.md), [Sensoren](SENSORS.md),
[Warnungscodes](WARNING_CODES.md) oder [Architektur und Datenverträgen](ARCHITECTURE.md).

Die Integration ist ein unabhängiges Community-Projekt. Der unten verlinkte
Veröffentlichungsstatus gilt auch für die hier beschriebenen Funktionen.

### Was bedeutet «Niederschlag (10 Minuten)»?

Das ist die zuletzt verfügbare **gemessene Menge eines Zehnminutenintervalls**.
Der Messzeitpunkt nennt dessen Ende. «12:20» bedeutet beispielsweise die zehn
Minuten bis 12:20; der Wert ist keine Live-Menge bis jetzt. Die verwendeten
Stationsdateien erscheinen alle 20 Minuten. Für vergangene Stunden gibt es
eine separate amtliche Niederschlagsstatistik. Einen zusätzlichen selbst
berechneten Wert «laufende Stunde» bietet der Fork nicht mehr an.
Beim alternativen Open-Meteo-Wetter ist die Menge modelliert; sie heisst
«Niederschlag (Modellintervall)» und enthält die Intervalllänge als Attribut.

## 1. Voraussetzungen prüfen

- Home Assistant **2026.8.3 oder neuer**, mit funktionierendem Internetzugang.
- HACS ist bereits eingerichtet. Falls nicht, nutze zuerst die
  [offizielle HACS-Anleitung](https://www.hacs.xyz/docs/use/download/download/).
- Lies den [Veröffentlichungsstatus in der README](../README.md#release-status).
  Installiere ausschliesslich eine dort freigegebene Version. Gibt es noch
  keine freigegebene Version, warte mit der Installation.
- Erstelle unter **Einstellungen → System → Backups** ein vollständiges
  Home-Assistant-Backup und lade eine Kopie herunter.
  Behalte den zugehörigen Wiederherstellungsschlüssel sicher auf.

Eine Vorabversion ist eine Testversion. Ein grüner GitHub-Testlauf allein macht
sie noch nicht zur freigegebenen Version für den Alltag.

## 2. Integration über HACS herunterladen

1. Öffne in der Seitenleiste **HACS**.
2. Öffne oben rechts das **Dreipunktmenü → Benutzerdefinierte Repositories**
   (englisch: **Custom repositories**).
3. Trage `https://github.com/martins-netizen/ha-meteoswiss` ein, wähle
   **Integration** und klicke **Hinzufügen / Add**.
4. Öffne den neuen Eintrag **MeteoSwiss (maintained fork)** und wähle
   **Herunterladen / Download**. Wähle ausdrücklich die freigegebene Version.
   Falls eine freigegebene Vorabversion ausgeblendet ist, aktiviere ihre Anzeige
   in HACS. Wird die Version weiterhin nicht angeboten, halte hier an.
   Wähle nicht ersatzweise einen Entwicklungsbranch.
5. Starte Home Assistant neu und warte, bis die Oberfläche wieder erreichbar ist.

Das Herunterladen stellt die Software bereit. Erst im nächsten Schritt legst
du fest, für welchen Ort sie Daten liefern soll.

## 3. Messstation und Warnort auswählen

Öffne **Einstellungen → Geräte & Dienste → Integration hinzufügen → MeteoSwiss**.

Für gemessene Schweizer Wetterdaten wählst du **MeteoSwiss STAC API
(Swiss Stations)**. Das ist die Stationsauswahl; du musst dich nicht mit der
zugrunde liegenden Schnittstelle beschäftigen. Belasse das Aktualisierungsintervall
für den Einstieg bei **600 Sekunden**.

Wähle eine Wetterstation und gib die **vierstellige Postleitzahl des Warnortes**
ein, zum Beispiel **8302**. Nicht den sechsstelligen internen App-Code eingeben.
Die Integration prüft die Wetterdatenquelle vor dem Speichern. Bei einem
Verbindungsfehler kannst du denselben Dialog später erneut absenden.

Diese Orte haben unterschiedliche Aufgaben:

| Angabe | Wofür sie verwendet wird |
|---|---|
| Wetterstation, z. B. Zürich / Kloten | Gemessene Temperatur, Regen, Wind und weitere Stationswerte |
| Postleitzahl | Auswahl der Wetter- und Naturgefahrenwarnungen |
| Standort von Home Assistant | Wetterprognose, modellierte Pollen und Luftqualität |
| Pollenmessstation | Gemessene Pollen; separat in den Integrationsoptionen wählen |

Die Postleitzahl wählt nicht automatisch die Wetterstation. Prüfe den
Home-Assistant-Standort unter **Einstellungen → System → Allgemein** und ändere
ihn nur, wenn er tatsächlich falsch ist: Auch andere Integrationen verwenden ihn.

**Alternative:** **Open-Meteo API (Free, Global)** liefert modelliertes aktuelles
Wetter an eingegebenen Koordinaten. Das ist eine bewusste andere Datenquelle,
keine automatische Reserve für die Schweizer Messstation. Die Warnungen bleiben
an die vierstellige Postleitzahl gebunden.

## 4. Pollenmessstation und erste Werte prüfen

Öffne bei der vorhandenen MeteoSwiss-Integration **Konfigurieren**. Wähle die
gewünschte Pollenmessstation; sie wird nicht automatisch aus der Wetterstation
abgeleitet. Der aktuelle Standard ist **Luzern (PLZ)**.

Öffne danach die Geräte der Integration. Du solltest Wetter, Messwerte, drei
Warnsensoren sowie Pollen-/Luftqualitätswerte finden. Die Wetterprognose zeigt
bis zu 24 Stunden und fünf Tage. Die erste Abfrage zusätzlicher Quellen läuft
im Hintergrund; deren Daten müssen nicht sofort gleichzeitig erscheinen.

| Anzeige | Bedeutung |
|---|---|
| `0` | Tatsächlicher Nullwert, z. B. kein gemessener Niederschlag |
| `unknown` / Unbekannt | Für diesen Einzelwert liegt kein verwendbarer Wert vor |
| `unavailable` / Nicht verfügbar | Die betreffende Datenquelle konnte nicht erfolgreich aktualisiert werden |
| Warnsensor aus | Keine passende Warnung in einem erfolgreich gelesenen Warnungsfeed |

Ein Föhnindex oder eine Schneehöhe kann unbekannt bleiben, weil die Station
diesen Wert nicht liefert. Ein unbekannter UV-Wert allein belegt keinen Ausfall
der übrigen Daten. Eine ausgefallene Warnungsquelle bedeutet keine Entwarnung.

## 5. Anzeige verwenden und Hilfe erhalten

Du kannst die Entitäten in vorhandenen Home-Assistant-Karten verwenden.
Ein eigenes Dashboard oder eine zusätzliche Karte ist für die Einrichtung
nicht erforderlich. Deutsch, Englisch, Französisch und Italienisch werden mitgeliefert;
manuell kopierte Übersetzungsdateien sind nicht nötig. Einige bestehende
Geräte-/Attributnamen und die Quellenauswahl behalten aus Kompatibilitätsgründen
englische Bezeichnungen.

Die Prognose verwendet **MeteoSwiss ICON Seamless über Open-Meteo**. Sie ist eine
Modellprognose, keine Messung an deinem Haus und keine garantierte Auswahl des
jeweils genauesten aller Wettermodelle. Die Luftqualitätswerte sind ebenfalls
Modellwerte und ersetzen keinen lokalen Luftsensor.

Bei Problemen: Integration nicht löschen und neu anlegen. Notiere Version,
Zeitpunkt und betroffenen Wert und verwende die [kurze Fehlerhilfe](USAGE.md#quick-troubleshooting)
oder [melde das Problem im Fork](https://github.com/martins-netizen/ha-meteoswiss/issues).
Für vertrauliche Sicherheitsmeldungen nutze
[Report a vulnerability](https://github.com/martins-netizen/ha-meteoswiss/security/advisories).

Weiterführend: [Sensoren](SENSORS.md), [technische Einstellungen](USAGE.md),
[offizielle HACS-Bedienung](https://www.hacs.xyz/docs/use/repositories/dashboard/).
