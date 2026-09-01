"""Phase 1: Ermittlung & Auskunft.

Nimmt einen neuen Fall auf: IP-Adresse (anonymisiert/Dummy), Werk, Zeitstempel und Status des
Gestattungsbeschlusses (§ 101 Abs. 9 UrhG). Ein Fall kann erst in Phase 2 (Abmahnung) übergehen,
wenn der Gestattungsbeschluss erteilt wurde.
"""

from __future__ import annotations

from datetime import datetime

from app.database import insert_fall
from app.models import Fall, FallStatus, GestattungsbeschlussStatus


def neuen_fall_anlegen(
    ip_adresse: str,
    werk: str,
    mandant: str,
    zeitstempel: datetime,
    gestattungsbeschluss_status: GestattungsbeschlussStatus,
    forderungshoehe_euro: float,
) -> Fall:
    fall = Fall(
        id=None,
        ip_adresse=ip_adresse,
        werk=werk,
        mandant=mandant,
        zeitstempel=zeitstempel,
        gestattungsbeschluss_status=gestattungsbeschluss_status,
        forderungshoehe_euro=forderungshoehe_euro,
        status=FallStatus.ERMITTLUNG,
    )
    return insert_fall(fall)


def bereit_fuer_abmahnung(fall: Fall) -> bool:
    """Ein Fall darf erst abgemahnt werden, wenn der Gestattungsbeschluss erteilt ist."""
    return (
        fall.status == FallStatus.ERMITTLUNG
        and fall.gestattungsbeschluss_status == GestattungsbeschlussStatus.ERTEILT
    )
