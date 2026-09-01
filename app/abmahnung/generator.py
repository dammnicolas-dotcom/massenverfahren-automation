"""Phase 2: Abmahnung.

Generiert ein Abmahnschreiben aus einer Markdown-Textvorlage. Es erfolgt kein echter Versand —
das Ergebnis wird als Markdown-Datei unter output/abmahnungen/ abgelegt. Setzt außerdem die
initiale Frist über die zentrale Fristverwaltung.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from app.database import update_fall
from app.ermittlung.intake import bereit_fuer_abmahnung
from app.fristverwaltung.fristverwaltung import setze_abmahnfrist
from app.models import Fall, FallStatus

TEMPLATE_PATH = Path(__file__).resolve().parent / "templates" / "abmahnung_template.md"
OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / "output" / "abmahnungen"


class FallNichtBereitError(Exception):
    """Der Fall darf noch nicht abgemahnt werden (Gestattungsbeschluss fehlt)."""


def abmahnung_erzeugen(fall: Fall) -> Fall:
    if not bereit_fuer_abmahnung(fall):
        raise FallNichtBereitError(
            f"Fall {fall.id}: Gestattungsbeschluss-Status "
            f"'{fall.gestattungsbeschluss_status.value}' erlaubt noch keine Abmahnung."
        )

    frist_datum = setze_abmahnfrist(datetime.utcnow())

    vorlage = TEMPLATE_PATH.read_text(encoding="utf-8")
    schreiben = vorlage.format(
        mandant=fall.mandant,
        fall_id=fall.id,
        datum=datetime.utcnow().date().isoformat(),
        ip_adresse=fall.ip_adresse,
        zeitstempel=fall.zeitstempel.isoformat(sep=" ", timespec="minutes"),
        werk=fall.werk,
        forderungshoehe_euro=fall.forderungshoehe_euro,
        frist_datum=frist_datum.isoformat(),
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    pfad = OUTPUT_DIR / f"abmahnung_fall_{fall.id}.md"
    pfad.write_text(schreiben, encoding="utf-8")

    fall.status = FallStatus.IN_FRISTUEBERWACHUNG
    fall.frist_datum = frist_datum
    fall.abmahnung_pfad = str(pfad.relative_to(OUTPUT_DIR.parent.parent))
    update_fall(fall)
    return fall
