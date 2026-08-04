# KNX Label Creator V2

**Version:** 2.0.0  
**Autor:** Christian Köppen  
**Unternehmen:** hbTec AG

KNX Label Creator ist eine webbasierte Anwendung, die physikalische Adressen und Gerätedaten aus ETS5- und ETS6-Projektdateien einliest und passende Druckdaten erzeugt.

## Funktionen

- ETS5- und ETS6-Projekte bis 500 MB einlesen
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

## Installation

Vorausgesetzt werden Docker und Docker Compose.

```bash
git clone https://github.com/chregu1973/KNX-Project-Tools-by-cko-hbTec.git
cd KNX-Project-Tools-by-cko-hbTec
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

- ETS-Projekte und Exporte liegen ausschließlich in den Docker-Volumes unter `data/` und werden nicht in Git aufgenommen.
- Über **Projekt löschen / Neues Projekt** werden das aktuelle Projekt, der Cache und die erzeugten Exporte entfernt.
- Version 2.0.0 verwaltet noch genau ein aktives Projekt pro Installation. Sie ist deshalb für eine eigene Installation beziehungsweise einen kontrollierten Testserver ausgelegt, nicht für einen öffentlichen Mehrbenutzerbetrieb.
- Eine automatische, sitzungsbezogene Löschung ist für eine spätere Version vorgesehen.

Für einen dauerhaft stabilen Flask-Sitzungsschlüssel kann beim Containerstart die Umgebungsvariable `SECRET_KEY` gesetzt werden. Ohne diese Variable erzeugt die Anwendung bei jedem Containerstart einen neuen zufälligen Schlüssel.

## Projektstruktur

```text
app/
├── assets/
├── core/
├── exporters/
├── static/
└── templates/

data/
├── uploads/
└── exports/
```

## Lizenz

Dieses Projekt steht unter der [MIT License](LICENSE).

© 2026 Christian Köppen
