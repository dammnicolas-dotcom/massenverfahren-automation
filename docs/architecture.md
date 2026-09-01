# Architektur: Case-Management für Filesharing-Massenabmahnverfahren

> Hinweis: Dieses Dokument wurde direkt aus der Aufgabenbeschreibung abgeleitet (es gab kein
> vorheriges Architektur-Dokument im Projekt). Es dient als Diskussionsgrundlage für den
> Prototyp, nicht als verbindliche Zielarchitektur.

## Kontext

Prototyp für den Case-Management-Workflow einer Kanzlei, die für Mandanten (z. B.
Gaming-Publisher) Filesharing-Urheberrechtsverletzungen verfolgt. Alle Daten im Prototyp sind
**fiktiv** (Test-IPs aus dem Dokumentations-Adressbereich nach RFC 5737, fiktive Werktitel und
Mandanten). Es werden keine echten Abmahnungen versendet und keine echten Personendaten
verarbeitet.

## Phasenmodell

```mermaid
flowchart TD
    A[Phase 1: Ermittlung & Auskunft] -->|Gestattungsbeschluss erteilt| B[Phase 2: Abmahnung]
    B --> C[Phase 3: Fristüberwachung & Triage]
    C -->|Grün: Routine-Reaktion| E1[Automatischer Fallabschluss]
    C -->|Gelb: Klärungsbedarf| E2[Manuelle Prüfung]
    C -->|Rot: Widerspruch| E3[Anwaltliche Bearbeitung]
    C -->|Keine Reaktion bis Frist| D[Phase 4: Eskalation]
    E3 --> D
    D -->|Neues Fristdatum: Mahnverfahren/Klage| C

    subgraph Zentrale Fristverwaltung
        F[(Fristenwächter-Modul: §§ 187-193 BGB, § 222 ZPO)]
    end
    B -. setzt initiale Frist .-> F
    C -. liest/aktualisiert Fristen .-> F
    D -. setzt neue Frist .-> F
```

## Module

Jede Phase ist ein eigenes Python-Package unter `app/`, kommunizierend über ein gemeinsames
`Fall`-Datenmodell (SQLite, siehe `app/models.py` / `app/database.py`):

| Modul | Verantwortung |
|---|---|
| `app/ermittlung/` | Fall-Intake: IP-Adresse (Dummy), Werk, Zeitstempel, Status Gestattungsbeschluss (§ 101 Abs. 9 UrhG) |
| `app/abmahnung/` | Generiert Abmahnschreiben aus Markdown-Textvorlage mit Platzhaltern; kein echter Versand |
| `app/fristverwaltung/` | Zentrale Fristverwaltung; vendored aus dem separaten `fristenwaechter`-Projekt (`frist_berechnung.py`, §§ 187-193 BGB / § 222 ZPO) |
| `app/triage/` | Regelbasierte Ampel-Klassifizierung eingehender Reaktionen (Grün/Gelb/Rot), konfigurierbar über `rules.py` |
| `app/eskalation/` | Setzt Fälle ohne Reaktion oder mit Rot-Status mit neuer Frist zurück in die Fristverwaltung |
| `app/main.py` | FastAPI-App, Web-Dashboard (Ampel-Übersicht aller Fälle) |

## Ampel-Logik (Phase 3)

Regelbasiert, konfigurierbar, keine ML-Blackbox — siehe `app/triage/rules.py`. Priorität bei
mehrdeutigen Treffern: **Rot > Gelb > Grün**. Struktur ist bewusst erweiterbar (Liste von
Regeln mit Farbe, Stichwörtern und Beschreibung), sodass später z. B. NLP-Klassifikatoren als
zusätzliche Regel-Quelle ergänzt werden könnten, ohne die Aufrufer anzupassen.

- **Grün (Routine):** bekannte Standardmuster (unterschriebene Unterlassungserklärung,
  Zahlungseingang) → automatischer Fallabschluss.
- **Gelb (Klärungsbedarf):** untypische Einwände, Minderjährigkeit des Anschlussinhabers,
  WLAN-Sicherungsfragen → Fall wird markiert, nicht automatisch entschieden.
- **Rot (Streitfall):** expliziter Widerspruch → zwingend an anwaltliche Bearbeitung.

## Eskalation (Phase 4)

Fälle, die bis zum Fristablauf keine Reaktion zeigen, oder die als Rot klassifiziert wurden und
anwaltlich final negativ beschieden sind, werden mit neuem Fristdatum (Mahnverfahren/Klage,
Standard: 3 Wochen) zurück in die zentrale Fristverwaltung überführt und laufen erneut durch
Phase 3.
