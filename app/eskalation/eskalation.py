"""Phase 4: Eskalation.

Fälle ohne Reaktion bis zum Fristablauf, oder mit Rot-Status (Widerspruch, anwaltlich final
negativ beschieden), werden mit neuem Fristdatum (Mahnverfahren/Klage) zurück in die zentrale
Fristverwaltung überführt und durchlaufen erneut Phase 3.
"""

from __future__ import annotations

from datetime import date

from app.database import update_fall
from app.fristverwaltung.fristverwaltung import frist_abgelaufen, setze_eskalationsfrist
from app.models import Ampel, Fall, FallStatus


class NichtEskalierbarError(Exception):
    """Der Fall erfüllt (noch) keine Eskalationsvoraussetzung."""


def eskalierbar(fall: Fall, heute: date | None = None) -> bool:
    if fall.status in (FallStatus.ABGESCHLOSSEN, FallStatus.ESKALIERT):
        return False
    keine_reaktion_und_frist_abgelaufen = fall.reaktion_text is None and frist_abgelaufen(
        fall.frist_datum, heute
    )
    return keine_reaktion_und_frist_abgelaufen or fall.ampel == Ampel.ROT


def eskalieren(fall: Fall, heute: date | None = None) -> Fall:
    if not eskalierbar(fall, heute):
        raise NichtEskalierbarError(
            f"Fall {fall.id} erfüllt keine Eskalationsvoraussetzung "
            "(weder Fristablauf ohne Reaktion noch Rot-Status)."
        )

    heute = heute or date.today()
    fall.frist_datum = setze_eskalationsfrist(heute)
    fall.status = FallStatus.ESKALIERT
    fall.eskalationsstufe += 1
    fall.notiz = (
        f"Eskaliert (Stufe {fall.eskalationsstufe}): Mahnverfahren/Klage, "
        f"neue Frist {fall.frist_datum.isoformat()}."
    )
    update_fall(fall)
    return fall
