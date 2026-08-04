# KNX Label Creator V2

**Version:** 2.1.2
**Autor:** Christian Köppen  
**Unternehmen:** hbTec AG

KNX Label Creator ist eine webbasierte Anwendung, die physikalische Adressen und Gerätedaten aus ETS5- und ETS6-Projektdateien einliest und passende Druckdaten erzeugt.

## Funktionen

- ETS5- und ETS6-Projekte bis 500 MB einlesen
- passwortgeschützte ETS-Projekte einlesen, ohne das Passwort zu speichern
- Projektübersicht und Liste aller physikalischen Adressen
- vollständiger CSV-Export der Geräteliste
- Geräte nach Bereich, Linie und Suchtext auswählen
- A4-Etiketten als PDF mit Vorschau, Startposition und optionalem Logo
- Vorlagen für Avery Zweckform 3422, 6122, 3652 und 3653
- benutzerdefinierte Etikettenformate
- Brother P-touch CSV für 6-mm-Band
- fertiges P-touch-Editor-Projekt (`.lbxs`) mit eingebetteter Datenbank
- DYMO LabelWriter 11354 als PDF im Format 57 × 32 mm
- CSV-Export für DYMO Connect
- geladenes Projekt und erzeugte Exporte manuell löschen
- getrennte Projekt- und Exportdaten für jeden Browser
- automatische Löschung aller Sitzungsdaten nach konfigurierbarer Inaktivität

## Installation

Vorausgesetzt werden Docker und Docker Compose.

```bash
git clone https://github.com/chregu1973/KNX-Project-Tools-by-cko-hbTec.git
cd KNX-Project-Tools-by-cko-hbTec
cp .env.example .env
# In .env unbedingt einen eigenen SECRET_KEY eintragen.
docker compose up --build -d
```

Danach im Browser öffnen:

```text
http://SERVER-IP:5002
```

Der externe Port kann in `docker-compose.yml` angepasst werden.

## P-touch-Hinweis

Der universelle CSV-Export kann im P-touch Editor importiert werden. Das fertige `.lbxs`-Projekt benötigt P-touch Editor 6.4 oder neuer und ist für 6-mm-Band vorbereitet. Die enthaltene Vorlage wurde mit einem Brother PT-P900W erstellt. Bei einem anderen Modell muss der Drucker im Editor möglicherweise einmal neu ausgewählt werden.

## DYMO-Hinweis

Das DYMO-PDF verwendet pro Seite exakt 57 × 32 mm. Im Druckdialog muss **Tatsächliche Grösse / 100 %** eingestellt sein.

## Daten und Datenschutz

- Jeder Browser erhält eine zufällige, signierte Sitzungskennung. Projektdateien, Cache und Exporte unterschiedlicher Nutzer werden strikt in getrennten Verzeichnissen verarbeitet.
- Im Cookie liegt nur die Sitzungskennung. Projektinhalt und Projektpasswort werden dort nicht gespeichert.
- ETS-Projekte und Exporte liegen ausschließlich unter `data/sessions/` und werden nicht in Git aufgenommen.
- Nach standardmäßig 60 Minuten ohne Aktivität löscht ein Hintergrundprozess das komplette Sitzungsverzeichnis. Die Frist ist mit `SESSION_TTL_MINUTES` konfigurierbar.
- Über **Projekt löschen / Neues Projekt** werden die Daten der eigenen Sitzung sofort entfernt. Andere Sitzungen bleiben unangetastet.
- Das Passwort eines geschützten ETS-Projekts wird nur im Arbeitsspeicher für den Import verwendet und niemals gespeichert.

Für den öffentlichen Betrieb muss in `.env` ein dauerhafter, zufälliger `SECRET_KEY` gesetzt werden. Hinter einer HTTPS-Verbindung sollte außerdem `SESSION_COOKIE_SECURE=true` aktiviert sein.

## Konfiguration

| Variable | Standard | Bedeutung |
| --- | ---: | --- |
| `SECRET_KEY` | zufällig je Containerstart | Signiert die Browser-Sitzung; produktiv dauerhaft setzen |
| `SESSION_TTL_MINUTES` | `60` | Löschung nach dieser Anzahl Minuten ohne Aktivität |
| `SESSION_CLEANUP_INTERVAL_SECONDS` | `300` | Prüfintervall der automatischen Bereinigung |
| `SESSION_COOKIE_SECURE` | `false` | Cookie nur über HTTPS senden; online auf `true` setzen |
| `SESSION_CLEANUP_ENABLED` | `true` | Hintergrundbereinigung aktivieren |

## Projektstruktur

```text
app/
├── assets/
├── core/
├── exporters/
├── static/
└── templates/

data/
└── sessions/
    └── <zufällige Sitzungskennung>/
        ├── uploads/
        ├── exports/
        ├── current_project.pkl
        └── .last_activity
```

## Lizenz

Dieses Projekt steht unter der [MIT License](LICENSE).

© 2026 Christian Köppen
