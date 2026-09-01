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

GRENZWERT_AMTSGERICHT_EUR = 10_000.0
"""Streitwertgrenze Amtsgericht/Landgericht nach § 23 Nr. 1 GVG.

Stand-Hinweis: Zum 1. Januar 2026 wurde diese Grenze durch das Gesetz vom 8. Dezember 2025
von 5.000 EUR auf 10.000 EUR angehoben (für ab diesem Zeitpunkt anhängig gemachte
Verfahren; für zuvor anhängig gemachte Altverfahren gilt weiterhin die alte Grenze von
5.000 EUR — hier nicht separat abgebildet, da der Prototyp keine Altfall-Unterscheidung
nach Verfahrensbeginn trifft).
"""


@dataclass(frozen=True)
class ZustaendigkeitsErgebnis:
    zustaendiges_gericht: str
    gerichtsstand_norm: str
    anwaltszwang: bool
    rechtsgrundlage_anwaltszwang: str
    kurzbegruendung: str


def pruefe_zustaendigkeit(
    ist_natuerliche_person: bool,
    gewerbliche_nutzung: bool,
    streitwert: float,
    wohnsitz_beklagter_plz: str | None = None,
) -> ZustaendigkeitsErgebnis:
    """Bestimmt Gerichtsstand, zuständiges Gericht und Anwaltszwang für eine Klage.

    Die sachliche Zuständigkeit (Amtsgericht vs. Landgericht, § 23 Nr. 1 GVG) und der
    daran gekoppelte Anwaltszwang (§ 78 Abs. 1 ZPO) hängen ausschließlich vom Streitwert
    ab und gelten unabhängig davon, welcher Gerichtsstand (§ 104a UrhG oder § 32 ZPO)
    einschlägig ist. `wohnsitz_beklagter_plz` fließt nicht in die Entscheidung ein und
    dient nur der Dokumentation im Aktenvermerk.
    """
    if streitwert < 0:
        raise ValueError("streitwert darf nicht negativ sein.")

    ist_landgericht = streitwert >= GRENZWERT_AMTSGERICHT_EUR
    gericht_ebene = "Landgericht" if ist_landgericht else "Amtsgericht"
    anwaltszwang = ist_landgericht  # § 78 Abs. 1 ZPO: Anwaltszwang nur vor dem Landgericht

    plz_hinweis = f" (Wohnsitz Beklagter PLZ {wohnsitz_beklagter_plz})" if wohnsitz_beklagter_plz else ""

    if not ist_natuerliche_person or gewerbliche_nutzung:
        grund = "keine natürliche Person" if not ist_natuerliche_person else "gewerbliche/berufliche Nutzung"
        return ZustaendigkeitsErgebnis(
            zustaendiges_gericht=f"{gericht_ebene} (fliegender Gerichtsstand, § 32 ZPO)",
            gerichtsstand_norm="§ 32 ZPO",
            anwaltszwang=anwaltszwang,
            rechtsgrundlage_anwaltszwang="§ 78 Abs. 1 ZPO",
            kurzbegruendung=(
                f"§ 104a UrhG greift nicht ({grund}) — Klage am Ort der Rechtsverletzung "
                f"bundesweit möglich (§ 32 ZPO). Bei einem Streitwert von "
                f"{streitwert:.2f} EUR ist das {gericht_ebene} sachlich zuständig "
                f"(§ 23 Nr. 1 GVG){plz_hinweis}."
            ),
        )

    return ZustaendigkeitsErgebnis(
        zustaendiges_gericht=f"{gericht_ebene} am Wohnsitz des Beklagten (§ 104a UrhG)",
        gerichtsstand_norm="§ 104a UrhG",
        anwaltszwang=anwaltszwang,
        rechtsgrundlage_anwaltszwang="§ 78 Abs. 1 ZPO",
        kurzbegruendung=(
            f"Natürliche Person ohne gewerbliche Nutzung — ausschließlicher Gerichtsstand "
            f"am Wohnsitz des Beklagten (§ 104a UrhG). Bei einem Streitwert von "
            f"{streitwert:.2f} EUR ist das {gericht_ebene} sachlich zuständig "
            f"(§ 23 Nr. 1 GVG), Anwaltszwang: {'ja' if anwaltszwang else 'nein'} "
            f"(§ 78 Abs. 1 ZPO){plz_hinweis}."
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

    ergebnis = pruefe_zustaendigkeit(
        ist_natuerliche_person, gewerbliche_nutzung, streitwert, wohnsitz_beklagter_plz
    )

    print("\n--- Ergebnis ---")
    print(f"Zuständiges Gericht:          {ergebnis.zustaendiges_gericht}")
    print(f"Gerichtsstand-Norm:           {ergebnis.gerichtsstand_norm}")
    print(f"Anwaltszwang:                 {'ja' if ergebnis.anwaltszwang else 'nein'}")
    print(f"Rechtsgrundlage Anwaltszwang: {ergebnis.rechtsgrundlage_anwaltszwang}")
    print(f"Kurzbegründung:               {ergebnis.kurzbegruendung}")


if __name__ == "__main__":
    cli()
