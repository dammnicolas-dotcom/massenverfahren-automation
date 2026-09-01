"""Fristberechnung nach § 222 ZPO i.V.m. §§ 187-193 BGB."""

from datetime import date, timedelta
from typing import Iterable, Optional


def berechne_frist(
    ereignis_datum: date,
    *,
    tage: Optional[int] = None,
    wochen: Optional[int] = None,
    monate: Optional[int] = None,
    feiertage: Iterable[date] = (),
) -> date:
    """Berechnet das Fristende nach § 222 ZPO i.V.m. §§ 187-193 BGB.

    ereignis_datum: Tag des fristauslösenden Ereignisses (z.B. Zustellung).
        Dieser Tag wird nach § 187 Abs. 1 BGB nicht mitgerechnet.
    tage/wochen/monate: genau eine dieser Einheiten angeben.
    feiertage: gesetzliche Feiertage am maßgeblichen Ort (Bundesland-abhängig),
        relevant für die Verschiebung nach § 222 Abs. 2 ZPO.
    """
    einheiten = [e for e in (tage, wochen, monate) if e is not None]
    if len(einheiten) != 1:
        raise ValueError("Genau eine Fristeinheit angeben: tage, wochen oder monate.")

    if tage is not None:
        # § 188 Abs. 1 BGB: Tagesfrist endet mit Ablauf des letzten Tages,
        # der Fristbeginn (Ereignis + 1 Tag) ist hier bereits eingerechnet.
        fristende = ereignis_datum + timedelta(days=tage)
    elif wochen is not None:
        fristende = ereignis_datum + timedelta(weeks=wochen)
    else:
        # § 188 Abs. 2 BGB: Monatsfrist endet am Tag mit derselben Zahl
        # im Zielmonat; § 188 Abs. 3 BGB regelt den Fall, dass dieser Tag
        # im Zielmonat nicht existiert (z.B. 31. -> Februar).
        fristende = _add_months(ereignis_datum, monate)

    feiertage_set = set(feiertage)
    # § 222 Abs. 2 ZPO: fällt das Fristende auf Samstag, Sonntag oder einen
    # gesetzlichen Feiertag, endet die Frist mit Ablauf des nächsten Werktages.
    while fristende.weekday() >= 5 or fristende in feiertage_set:
        fristende += timedelta(days=1)

    return fristende


def _add_months(d: date, months: int) -> date:
    monat_index = d.month - 1 + months
    jahr = d.year + monat_index // 12
    monat = monat_index % 12 + 1
    tag = min(d.day, _letzter_tag_im_monat(jahr, monat))
    return date(jahr, monat, tag)


def _letzter_tag_im_monat(jahr: int, monat: int) -> int:
    if monat == 12:
        naechster_monat_erster = date(jahr + 1, 1, 1)
    else:
        naechster_monat_erster = date(jahr, monat + 1, 1)
    return (naechster_monat_erster - timedelta(days=1)).day


if __name__ == "__main__":
    # Beispiel: Zustellung am Montag, 3.8.2026, Frist von zwei Wochen (§ 517 ZPO)
    zustellung = date(2026, 8, 3)
    print(berechne_frist(zustellung, wochen=2))
