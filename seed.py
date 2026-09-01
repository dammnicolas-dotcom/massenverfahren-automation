"""Seed-Skript: legt Dummy-Fälle für den Prototyp an.

Alle Daten sind fiktiv. IP-Adressen stammen aus den für Dokumentation reservierten Bereichen
nach RFC 5737 (192.0.2.0/24, 198.51.100.0/24, 203.0.113.0/24) und sind keine echten Adressen.

Ausführen mit: python seed.py
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

from app.abmahnung.generator import abmahnung_erzeugen
from app.database import reset_db
from app.eskalation.eskalation import eskalieren
from app.ermittlung.intake import neuen_fall_anlegen
from app.fristverwaltung.fristverwaltung import setze_abmahnfrist
from app.models import GestattungsbeschlussStatus
from app.triage.klassifizierung import reaktion_registrieren


def vor_tagen(tage: int) -> datetime:
    return datetime.utcnow() - timedelta(days=tage)


def main() -> None:
    reset_db()

    # 1) Frisch in Ermittlung, Gestattungsbeschluss noch beantragt -> noch nicht abmahnbar.
    neuen_fall_anlegen(
        ip_adresse="203.0.113.11",
        werk="Sternenfeuer Legends",
        mandant="Nordlicht Games GmbH",
        zeitstempel=vor_tagen(2),
        gestattungsbeschluss_status=GestattungsbeschlussStatus.BEANTRAGT,
        forderungshoehe_euro=950.00,
    )

    # 2) Gestattungsbeschluss abgelehnt -> Fall bleibt in Ermittlung, keine Abmahnung möglich.
    neuen_fall_anlegen(
        ip_adresse="198.51.100.24",
        werk="Drachenherz Online",
        mandant="Pixelburg Interactive",
        zeitstempel=vor_tagen(10),
        gestattungsbeschluss_status=GestattungsbeschlussStatus.ABGELEHNT,
        forderungshoehe_euro=780.00,
    )

    # 3) Grün: Unterlassungserklärung + Zahlung eingegangen -> automatischer Abschluss.
    fall3 = neuen_fall_anlegen(
        ip_adresse="192.0.2.45",
        werk="Sternenfeuer Legends",
        mandant="Nordlicht Games GmbH",
        zeitstempel=vor_tagen(20),
        gestattungsbeschluss_status=GestattungsbeschlussStatus.ERTEILT,
        forderungshoehe_euro=850.00,
    )
    abmahnung_erzeugen(fall3)
    reaktion_registrieren(
        fall3,
        "Anbei die unterschriebene Unterlassungserklärung, die Zahlung wurde bereits überwiesen.",
    )

    # 4) Gelb: WLAN-Sicherungsfrage -> manuelle Prüfung.
    fall4 = neuen_fall_anlegen(
        ip_adresse="203.0.113.77",
        werk="Kolonie Mars-9",
        mandant="Rotstern Studios",
        zeitstempel=vor_tagen(18),
        gestattungsbeschluss_status=GestattungsbeschlussStatus.ERTEILT,
        forderungshoehe_euro=690.00,
    )
    abmahnung_erzeugen(fall4)
    reaktion_registrieren(
        fall4,
        "Unser WLAN war zum fraglichen Zeitpunkt nach aktuellem Stand der Technik gesichert, das war nicht ich.",
    )

    # 5) Gelb: Minderjährigkeit des Anschlussinhabers.
    fall5 = neuen_fall_anlegen(
        ip_adresse="198.51.100.90",
        werk="Turnier der Klingen",
        mandant="Achteck Verlag",
        zeitstempel=vor_tagen(15),
        gestattungsbeschluss_status=GestattungsbeschlussStatus.ERTEILT,
        forderungshoehe_euro=850.00,
    )
    abmahnung_erzeugen(fall5)
    reaktion_registrieren(fall5, "Mein Sohn ist minderjährig und hat das ohne unser Wissen getan.")

    # 6) Rot: expliziter Widerspruch -> anwaltliche Bearbeitung.
    fall6 = neuen_fall_anlegen(
        ip_adresse="192.0.2.133",
        werk="Kolonie Mars-9",
        mandant="Rotstern Studios",
        zeitstempel=vor_tagen(25),
        gestattungsbeschluss_status=GestattungsbeschlussStatus.ERTEILT,
        forderungshoehe_euro=920.00,
    )
    abmahnung_erzeugen(fall6)
    reaktion_registrieren(
        fall6,
        "Wir widersprechen der Forderung vollumfänglich und haben bereits unsere Anwältin eingeschaltet.",
    )

    # 7) Abgemahnt, Frist bereits abgelaufen, keine Reaktion -> eskalierbar.
    fall7 = neuen_fall_anlegen(
        ip_adresse="203.0.113.201",
        werk="Sternenfeuer Legends",
        mandant="Nordlicht Games GmbH",
        zeitstempel=vor_tagen(40),
        gestattungsbeschluss_status=GestattungsbeschlussStatus.ERTEILT,
        forderungshoehe_euro=850.00,
    )
    fall7 = abmahnung_erzeugen(fall7)
    fall7.frist_datum = date.today() - timedelta(days=3)
    from app.database import update_fall

    update_fall(fall7)

    # 8) Bereits eskaliert (Stufe 1), neue Frist läuft.
    fall8 = neuen_fall_anlegen(
        ip_adresse="198.51.100.150",
        werk="Turnier der Klingen",
        mandant="Achteck Verlag",
        zeitstempel=vor_tagen(55),
        gestattungsbeschluss_status=GestattungsbeschlussStatus.ERTEILT,
        forderungshoehe_euro=850.00,
    )
    fall8 = abmahnung_erzeugen(fall8)
    fall8.frist_datum = date.today() - timedelta(days=1)
    update_fall(fall8)
    eskalieren(fall8)

    # 9) Frisch abgemahnt, Frist läuft noch, keine Reaktion bisher.
    fall9 = neuen_fall_anlegen(
        ip_adresse="192.0.2.210",
        werk="Drachenherz Online",
        mandant="Pixelburg Interactive",
        zeitstempel=vor_tagen(3),
        gestattungsbeschluss_status=GestattungsbeschlussStatus.ERTEILT,
        forderungshoehe_euro=780.00,
    )
    abmahnung_erzeugen(fall9)

    print("Seed abgeschlossen: 9 fiktive Fälle angelegt.")
    print(f"Beispiel-Frist (Abmahnung ab heute): {setze_abmahnfrist(datetime.utcnow())}")


if __name__ == "__main__":
    main()
