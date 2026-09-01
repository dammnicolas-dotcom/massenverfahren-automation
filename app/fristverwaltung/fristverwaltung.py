"""Zentrale Fristverwaltung.

Jede Phase, die eine Frist setzt (Abmahnung, Eskalation), ruft ausschließlich diese
Schnittstelle auf. Die eigentliche Fristberechnung (§§ 187-193 BGB, § 222 ZPO) stammt aus dem
vendored `frist_berechnung`-Modul des separaten `fristenwaechter`-Projekts.
"""

from __future__ import annotations

from datetime import date, datetime

from app.fristverwaltung.frist_berechnung import berechne_frist

# Bundesland-abhängige Feiertage müssten im Produktivbetrieb je nach Gerichtsort/Wohnsitz
# gepflegt werden; für den Prototyp genügt eine leere Menge (siehe README/Hinweis der
# Fristenwächter-Dokumentation).
FEIERTAGE: set[date] = set()

ABMAHNFRIST_TAGE = 14
ESKALATIONSFRIST_WOCHEN = 3


def setze_abmahnfrist(ereignis_datum: date | datetime) -> date:
    """Frist ab Versand der Abmahnung (Standard: 2 Wochen)."""
    d = ereignis_datum.date() if isinstance(ereignis_datum, datetime) else ereignis_datum
    return berechne_frist(d, tage=ABMAHNFRIST_TAGE, feiertage=FEIERTAGE)


def setze_eskalationsfrist(ereignis_datum: date | datetime) -> date:
    """Neue Frist bei Eskalation (Mahnverfahren/Klage, Standard: 3 Wochen)."""
    d = ereignis_datum.date() if isinstance(ereignis_datum, datetime) else ereignis_datum
    return berechne_frist(d, wochen=ESKALATIONSFRIST_WOCHEN, feiertage=FEIERTAGE)


def frist_abgelaufen(frist_datum: date | None, heute: date | None = None) -> bool:
    if frist_datum is None:
        return False
    heute = heute or date.today()
    return heute > frist_datum
