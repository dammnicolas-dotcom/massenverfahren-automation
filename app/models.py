"""Gemeinsames Datenmodell für einen Fall (Filesharing-Massenabmahnverfahren).

Alle Werte sind für den Prototyp als fiktive Testdaten zu verstehen.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum


class GestattungsbeschlussStatus(str, Enum):
    BEANTRAGT = "beantragt"
    ERTEILT = "erteilt"
    ABGELEHNT = "abgelehnt"


class FallStatus(str, Enum):
    ERMITTLUNG = "ermittlung"
    ABMAHNUNG_VERSENDET = "abmahnung_versendet"
    IN_FRISTUEBERWACHUNG = "in_fristueberwachung"
    ESKALIERT = "eskaliert"
    ABGESCHLOSSEN = "abgeschlossen"


class Ampel(str, Enum):
    GRUEN = "gruen"
    GELB = "gelb"
    ROT = "rot"
    UNBEKANNT = "unbekannt"


@dataclass
class Fall:
    id: int | None
    ip_adresse: str
    werk: str
    mandant: str
    zeitstempel: datetime
    gestattungsbeschluss_status: GestattungsbeschlussStatus
    forderungshoehe_euro: float
    status: FallStatus = FallStatus.ERMITTLUNG
    ampel: Ampel = Ampel.UNBEKANNT
    frist_datum: date | None = None
    reaktion_text: str | None = None
    abmahnung_pfad: str | None = None
    eskalationsstufe: int = 0
    notiz: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
