"""Phase 3: Fristüberwachung & Triage.

Regelbasierte Ampel-Klassifizierung eingehender Reaktionen (Grün/Gelb/Rot). Grüne Fälle werden
automatisch abgeschlossen; Gelb wird zur Prüfung markiert; Rot geht zwingend an anwaltliche
Bearbeitung. Kein Fall wird bei Gelb oder Rot automatisch *entschieden* — nur automatisch
*einsortiert*.
"""

from __future__ import annotations

from app.database import update_fall
from app.models import Ampel, Fall, FallStatus
from app.triage.rules import PRIORITAET, REGELN


def klassifiziere_reaktion(text: str) -> Ampel:
    text_normalisiert = text.lower()

    treffer: set[Ampel] = set()
    for regel in REGELN:
        if any(stichwort in text_normalisiert for stichwort in regel.stichwoerter):
            treffer.add(regel.farbe)

    for farbe in PRIORITAET:
        if farbe in treffer:
            return farbe

    return Ampel.UNBEKANNT


def reaktion_registrieren(fall: Fall, reaktion_text: str) -> Fall:
    """Registriert eine eingehende Reaktion und klassifiziert sie regelbasiert."""
    fall.reaktion_text = reaktion_text
    fall.ampel = klassifiziere_reaktion(reaktion_text)

    if fall.ampel == Ampel.GRUEN:
        fall.status = FallStatus.ABGESCHLOSSEN
        fall.notiz = "Automatisch abgeschlossen: Standardmuster erkannt (Grün)."
    elif fall.ampel == Ampel.GELB:
        fall.notiz = "Zur manuellen Prüfung markiert: untypischer Einwand (Gelb)."
    elif fall.ampel == Ampel.ROT:
        fall.notiz = "An anwaltliche Bearbeitung übergeben: Widerspruch (Rot)."
    else:
        fall.notiz = "Reaktion konnte keinem Regelmuster zugeordnet werden — manuelle Prüfung erforderlich."
        fall.ampel = Ampel.GELB

    update_fall(fall)
    return fall
