"""Konfigurierbares Regelwerk für die Ampel-Klassifizierung eingehender Reaktionen.

Bewusst einfach gehalten (Keyword-Matching, case-insensitive), aber strukturiert als Liste von
Regeln, damit die Engine später erweiterbar ist (z. B. um ein Klassifikationsmodell als
zusätzliche Regel-Quelle), ohne dass `klassifizierung.py` angepasst werden muss.

Priorität bei mehreren Treffern: ROT > GELB > GRUEN (siehe klassifizierung.py).
"""

from __future__ import annotations

from dataclasses import dataclass

from app.models import Ampel


@dataclass(frozen=True)
class Regel:
    farbe: Ampel
    stichwoerter: tuple[str, ...]
    beschreibung: str


REGELN: tuple[Regel, ...] = (
    Regel(
        farbe=Ampel.ROT,
        stichwoerter=(
            "widerspruch",
            "widerspreche",
            "bestreite",
            "lehne ab",
            "weise zurück",
            "weise ich zurück",
            "anwalt eingeschaltet",
            "unsere anwältin",
            "unser anwalt",
        ),
        beschreibung="Expliziter Widerspruch -> zwingend anwaltliche Bearbeitung.",
    ),
    Regel(
        farbe=Ampel.GELB,
        stichwoerter=(
            "minderjährig",
            "minderjaehrig",
            "kind hat",
            "meine tochter",
            "mein sohn",
            "wlan",
            "w-lan",
            "gesichert",
            "nicht ich",
            "war ich nicht",
            "kenne mich nicht aus",
        ),
        beschreibung="Untypischer Einwand -> manuelle Prüfung, keine Automatik-Entscheidung.",
    ),
    Regel(
        farbe=Ampel.GRUEN,
        stichwoerter=(
            "unterlassungserklärung",
            "unterlassungserklaerung",
            "unterschrieben",
            "beigefügt",
            "beigefuegt",
            "überwiesen",
            "ueberwiesen",
            "zahlung erfolgt",
            "gezahlt",
            "anbei die erklärung",
        ),
        beschreibung="Bekanntes Standardmuster -> automatischer Fallabschluss.",
    ),
)

PRIORITAET: tuple[Ampel, ...] = (Ampel.ROT, Ampel.GELB, Ampel.GRUEN)
