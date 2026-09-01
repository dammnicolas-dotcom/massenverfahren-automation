# Massenverfahren Automation (Prototyp)

Prototyp für einen automatisierten Case-Management-Workflow für
Filesharing-Massenabmahnverfahren (Urheberrecht, Gaming-Publisher als fiktive Mandanten).

**Kein Produktivsystem.** Keine Anbindung an echte Mandantendaten, keine echten Personendaten,
kein echter Versand von Schreiben. Alle Fälle im Seed-Skript sind fiktiv; IP-Adressen stammen
aus den für Dokumentation reservierten Adressbereichen nach RFC 5737.

Fachlicher Hintergrund: [TALKING-POINT.md](TALKING-POINT.md)
Architektur (Mermaid-Flowchart, Modulübersicht): [docs/architecture.md](docs/architecture.md)

## Module (eines je Phase)

- `app/ermittlung/` — Phase 1: Fall-Intake
- `app/abmahnung/` — Phase 2: Abmahnschreiben aus Vorlage
- `app/fristverwaltung/` — zentrale Fristverwaltung (vendored aus dem separaten
  `fristenwaechter`-Projekt: §§ 187-193 BGB, § 222 ZPO)
- `app/triage/` — Phase 3: regelbasierte Ampel-Klassifizierung eingehender Reaktionen
- `app/eskalation/` — Phase 4: Eskalation bei Fristablauf ohne Reaktion oder Rot-Status
- `app/main.py` — FastAPI-App, Web-Dashboard

## Prototyp starten

Voraussetzung: Python 3.11+.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Dummy-Fälle anlegen (5–10 fiktive Testfälle, überschreibt die lokale SQLite-Datenbank):

```bash
python seed.py
```

Server starten:

```bash
uvicorn app.main:app --reload
```

Dashboard öffnen: [http://localhost:8000](http://localhost:8000)

Auf dem Dashboard lassen sich neue Fälle anlegen; auf der Detailseite eines Falls (`/faelle/{id}`)
kann eine Abmahnung erzeugt, eine eingehende Reaktion erfasst (wird automatisch nach
Ampelfarbe klassifiziert) und ein Fall eskaliert werden.

Tests für die Fristberechnung ausführen:

```bash
python -m unittest discover -s tests
```
