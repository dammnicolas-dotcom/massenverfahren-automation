# Massenverfahren Automation (Prototyp)

Erster Prototyp für einen automatisierten Case-Management-Workflow für
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
- `app/zustaendigkeit/` — Zuständigkeits-Checker für eine gerichtliche Geltendmachung
  (Gerichtsstand, Amtsgericht/Landgericht, Anwaltszwang; siehe Abschnitt unten)
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

Tests ausführen (Fristberechnung + Zuständigkeits-Checker):

```bash
python -m unittest discover -s tests
```

## Zuständigkeits-Checker

Bestimmt für eine mögliche Klage gegen den Anschlussinhaber Gerichtsstand, sachlich
zuständiges Gericht und Anwaltszwang, auf Basis von:

- [§ 104a UrhG](https://www.gesetze-im-internet.de/urhg/__104a.html) — ausschließlicher
  Gerichtsstand am Wohnsitz des Beklagten, wenn dieser eine natürliche Person ist, die das
  Werk nicht gewerblich/beruflich genutzt hat; sonst gilt der allgemeine "fliegende
  Gerichtsstand" nach [§ 32 ZPO](https://www.gesetze-im-internet.de/zpo/__32.html).
- [§ 23 Nr. 1 GVG](https://www.gesetze-im-internet.de/gvg/__23.html) — Streitwertgrenze
  zwischen Amtsgericht und Landgericht, aktuell 10.000 EUR (seit 1.1.2026 angehoben von
  zuvor 5.000 EUR). Für vor diesem Stichtag anhängig gemachte Altverfahren gilt weiterhin
  die alte Grenze von 5.000 EUR — steuerbar über den optionalen Parameter
  `verfahrensbeginn` von `pruefe_zustaendigkeit()`; ohne Angabe wird die aktuelle Grenze
  angenommen. Konstanten: `GRENZWERT_AMTSGERICHT_EUR_AB_REFORM`,
  `GRENZWERT_AMTSGERICHT_EUR_VOR_REFORM`, `STICHTAG_GVG_REFORM` in
  `app/zustaendigkeit/zustaendigkeit_checker.py`.
- [§ 78 Abs. 1 ZPO](https://www.gesetze-im-internet.de/zpo/__78.html) — Anwaltszwang vor
  dem Landgericht, nicht vor dem Amtsgericht.

Live-Demo per CLI:

```bash
python -m app.zustaendigkeit.zustaendigkeit_checker
```

Als Bibliotheksfunktion:

```python
from app.zustaendigkeit.zustaendigkeit_checker import pruefe_zustaendigkeit

ergebnis = pruefe_zustaendigkeit(
    ist_natuerliche_person=True, gewerbliche_nutzung=False, streitwert=4500.0
)
print(ergebnis.zustaendiges_gericht)  # "Amtsgericht am Wohnsitz des Beklagten (§ 104a UrhG)"
```
