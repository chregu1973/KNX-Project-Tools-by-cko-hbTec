# KNX Project Tools

**Version:** 1.1.0

**Autor:** Christian Köppen  
**Unternehmen:** hbTec AG

KNX Project Tools ist eine webbasierte Anwendung zur Erstellung von Beschriftungen, Etiketten und Auswertungen aus ETS5- und ETS6-Projektdateien.

---

## Funktionen

- ETS5- und ETS6-Projekte laden
- Dashboard mit Projektübersicht
- Physikalische Adressen anzeigen und als CSV exportieren
- Brother P-touch CSV-Export
- Filter nach Bereich und Linie
- Verpackungsetiketten als PDF
- A4-Vorschau für Verpackungsetiketten

---

## Installation

### Voraussetzungen

- Docker
- Docker Compose

### Projekt starten

```bash
docker compose up --build -d
```

Anschließend im Browser öffnen:

```text
http://SERVER-IP:5000
```

---

## Projektstruktur

```text
app/
├── core/
│   ├── knx_project.py
│   ├── models.py
│   ├── project_manager.py
│   └── xml_reader.py
│
├── exporters/
│   ├── csv_export.py
│   ├── label_pdf.py
│   └── ptouch_export.py
│
├── static/
│   ├── css/
│   └── js/
│
└── templates/

data/
├── uploads/
└── exports/
```

---

## Hinweise

- Es wird immer nur das zuletzt geladene ETS-Projekt gespeichert.
- Exportdateien werden lokal erzeugt.
- ETS-Projekte und erzeugte Exportdateien werden nicht im Git-Repository gespeichert.

---

## Screenshots

Werden mit einer späteren Version ergänzt.

---

## Lizenz

Dieses Projekt steht unter der **MIT License**.

© 2026 Christian Köppen
