"""Zuständigkeits-Checker für die gerichtliche Geltendmachung (Mahnverfahren/Klage).

Bestimmt Gerichtsstand, sachlich zuständiges Gericht (Amtsgericht/Landgericht) und
Anwaltszwang für eine mögliche Klage gegen den Anschlussinhaber, basierend auf:

- § 104a UrhG: ausschließlicher Gerichtsstand am Wohnsitz des Beklagten, wenn dieser eine
  natürliche Person ist, die das Werk nicht für ihre gewerbliche oder selbständige
  berufliche Tätigkeit genutzt hat. Andernfalls gilt der allgemeine "fliegende
  Gerichtsstand" des § 32 ZPO (Ort der Rechtsverletzung).
- § 23 Nr. 1 GVG: Streitwertgrenze zwischen Amtsgericht und Landgericht.
- § 78 Abs. 1 ZPO: Anwaltszwang vor dem Landgericht, nicht vor dem Amtsgericht.

Wird typischerweise in Phase 4 (Eskalation) aufgerufen, sobald eine gerichtliche
Geltendmachung ansteht — ist aber als eigenständiges Modul gehalten (analog zu
`app/fristverwaltung/`), da die Zuständigkeitsfrage unabhängig vom Fall-Lebenszyklus ist.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

STICHTAG_GVG_REFORM = date(2026, 1, 1)
"""Stichtag der GVG-Reform (Gesetz vom 8. Dezember 2025): maßgeblich ist der Zeitpunkt,
zu dem das Verfahren anhängig gemacht wurde (nicht das Datum der Streitwert-Prüfung)."""

GRENZWERT_AMTSGERICHT_EUR_VOR_REFORM = 5_000.0
"""Streitwertgrenze Amtsgericht/Landgericht (§ 23 Nr. 1 GVG) für vor dem 1.1.2026
anhängig gemachte Altverfahren."""

GRENZWERT_AMTSGERICHT_EUR_AB_REFORM = 10_000.0
"""Streitwertgrenze Amtsgericht/Landgericht (§ 23 Nr. 1 GVG) für ab dem 1.1.2026
anhängig gemachte Verfahren — aktuelle Rechtslage."""

GRENZWERT_AMTSGERICHT_EUR = GRENZWERT_AMTSGERICHT_EUR_AB_REFORM
"""Alias auf die aktuell geltende Grenze, für Aufrufer ohne Bezug zu einem konkreten
Verfahrensbeginn (z. B. Neufälle)."""


@dataclass(frozen=True)
class ZustaendigkeitsErgebnis:
    zustaendiges_gericht: str
    gerichtsstand_norm: str
    anwaltszwang: bool
    rechtsgrundlage_anwaltszwang: str
    kurzbegruendung: str
    angewandte_streitwertgrenze_eur: float


def _grenzwert_amtsgericht(verfahrensbeginn: date | None) -> float:
    """Wählt die zum Verfahrensbeginn geltende Streitwertgrenze (§ 23 Nr. 1 GVG).

    Ohne Angabe wird von einem ab dem Stichtag anhängig gemachten (Neu-)Verfahren
    ausgegangen. Vor dem 1.1.2026 anhängig gemachte Altverfahren behalten die bisherige
    Grenze von 5.000 EUR, unabhängig vom heutigen Prüfdatum.
    """
    if verfahrensbeginn is not None and verfahrensbeginn < STICHTAG_GVG_REFORM:
        return GRENZWERT_AMTSGERICHT_EUR_VOR_REFORM
    return GRENZWERT_AMTSGERICHT_EUR_AB_REFORM


def pruefe_zustaendigkeit(
    ist_natuerliche_person: bool,
    gewerbliche_nutzung: bool,
    streitwert: float,
    wohnsitz_beklagter_plz: str | None = None,
    verfahrensbeginn: date | datetime | None = None,
) -> ZustaendigkeitsErgebnis:
    """Bestimmt Gerichtsstand, zuständiges Gericht und Anwaltszwang für eine Klage.

    Die sachliche Zuständigkeit (Amtsgericht vs. Landgericht, § 23 Nr. 1 GVG) und der
    daran gekoppelte Anwaltszwang (§ 78 Abs. 1 ZPO) hängen vom Streitwert und von der
    zum Verfahrensbeginn geltenden Streitwertgrenze ab; beides gilt unabhängig davon,
    welcher Gerichtsstand (§ 104a UrhG oder § 32 ZPO) einschlägig ist.
    `wohnsitz_beklagter_plz` fließt nicht in die Entscheidung ein und dient nur der
    Dokumentation im Aktenvermerk. `verfahrensbeginn` steuert, ob die aktuelle Grenze
    (10.000 EUR, ab 1.1.2026) oder die Altfall-Grenze (5.000 EUR, davor anhängig
    gemachte Verfahren) angewandt wird; ohne Angabe wird die aktuelle Grenze angenommen.
    """
    if streitwert < 0:
        raise ValueError("streitwert darf nicht negativ sein.")

    verfahrensbeginn_datum = (
        verfahrensbeginn.date() if isinstance(verfahrensbeginn, datetime) else verfahrensbeginn
    )
    grenzwert = _grenzwert_amtsgericht(verfahrensbeginn_datum)
    ist_altfall = verfahrensbeginn_datum is not None and verfahrensbeginn_datum < STICHTAG_GVG_REFORM

    ist_landgericht = streitwert >= grenzwert
    gericht_ebene = "Landgericht" if ist_landgericht else "Amtsgericht"
    anwaltszwang = ist_landgericht  # § 78 Abs. 1 ZPO: Anwaltszwang nur vor dem Landgericht

    plz_hinweis = f" (Wohnsitz Beklagter PLZ {wohnsitz_beklagter_plz})" if wohnsitz_beklagter_plz else ""
    grenzwert_hinweis = (
        f"Grenze {grenzwert:.0f} EUR"
        + (
            f" — Altverfahren, anhängig vor dem {STICHTAG_GVG_REFORM.strftime('%d.%m.%Y')}"
            if ist_altfall
            else ""
        )
    )

    if not ist_natuerliche_person or gewerbliche_nutzung:
        grund = "keine natürliche Person" if not ist_natuerliche_person else "gewerbliche/berufliche Nutzung"
        return ZustaendigkeitsErgebnis(
            zustaendiges_gericht=f"{gericht_ebene} (fliegender Gerichtsstand, § 32 ZPO)",
            gerichtsstand_norm="§ 32 ZPO",
            anwaltszwang=anwaltszwang,
            rechtsgrundlage_anwaltszwang="§ 78 Abs. 1 ZPO",
            angewandte_streitwertgrenze_eur=grenzwert,
            kurzbegruendung=(
                f"§ 104a UrhG greift nicht ({grund}) — Klage am Ort der Rechtsverletzung "
                f"bundesweit möglich (§ 32 ZPO). Bei einem Streitwert von "
                f"{streitwert:.2f} EUR ist das {gericht_ebene} sachlich zuständig "
                f"(§ 23 Nr. 1 GVG, {grenzwert_hinweis}){plz_hinweis}."
            ),
        )

    return ZustaendigkeitsErgebnis(
        zustaendiges_gericht=f"{gericht_ebene} am Wohnsitz des Beklagten (§ 104a UrhG)",
        gerichtsstand_norm="§ 104a UrhG",
        anwaltszwang=anwaltszwang,
        rechtsgrundlage_anwaltszwang="§ 78 Abs. 1 ZPO",
        angewandte_streitwertgrenze_eur=grenzwert,
        kurzbegruendung=(
            f"Natürliche Person ohne gewerbliche Nutzung — ausschließlicher Gerichtsstand "
            f"am Wohnsitz des Beklagten (§ 104a UrhG). Bei einem Streitwert von "
            f"{streitwert:.2f} EUR ist das {gericht_ebene} sachlich zuständig "
            f"(§ 23 Nr. 1 GVG, {grenzwert_hinweis}), Anwaltszwang: "
            f"{'ja' if anwaltszwang else 'nein'} (§ 78 Abs. 1 ZPO){plz_hinweis}."
        ),
    )


def _frage_ja_nein(prompt: str) -> bool:
    antwort = input(f"{prompt} [j/n]: ").strip().lower()
    return antwort in ("j", "ja", "y", "yes")


def cli() -> None:
    """Einfache interaktive CLI zur Live-Vorführung an einem Fallbeispiel."""
    print("Zuständigkeits-Checker für Filesharing-Abmahnverfahren\n")
    ist_natuerliche_person = _frage_ja_nein("Ist der/die Beklagte eine natürliche Person?")
    gewerbliche_nutzung = _frage_ja_nein("Erfolgte eine gewerbliche/berufliche Nutzung des Werks?")
    streitwert = float(input("Streitwert in EUR: ").strip().replace(",", "."))
    plz_eingabe = input("PLZ Wohnsitz Beklagter (optional, Enter zum Überspringen): ").strip()
    wohnsitz_beklagter_plz = plz_eingabe or None
    verfahrensbeginn_eingabe = input(
        "Verfahrensbeginn (JJJJ-MM-TT, leer = aktuelle Grenze von "
        f"{GRENZWERT_AMTSGERICHT_EUR_AB_REFORM:.0f} EUR annehmen): "
    ).strip()
    verfahrensbeginn = date.fromisoformat(verfahrensbeginn_eingabe) if verfahrensbeginn_eingabe else None

    ergebnis = pruefe_zustaendigkeit(
        ist_natuerliche_person, gewerbliche_nutzung, streitwert, wohnsitz_beklagter_plz, verfahrensbeginn
    )

    print("\n--- Ergebnis ---")
    print(f"Zuständiges Gericht:          {ergebnis.zustaendiges_gericht}")
    print(f"Gerichtsstand-Norm:           {ergebnis.gerichtsstand_norm}")
    print(f"Angewandte Streitwertgrenze:  {ergebnis.angewandte_streitwertgrenze_eur:.0f} EUR")
    print(f"Anwaltszwang:                 {'ja' if ergebnis.anwaltszwang else 'nein'}")
    print(f"Rechtsgrundlage Anwaltszwang: {ergebnis.rechtsgrundlage_anwaltszwang}")
    print(f"Kurzbegründung:               {ergebnis.kurzbegruendung}")


if __name__ == "__main__":
    cli()
