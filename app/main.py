"""FastAPI-App: verbindet die vier Phasen-Module und stellt ein Web-Dashboard bereit.

Das Dashboard zeigt den aktuellen Status aller Fälle nach Ampelfarbe. Alle Schreib-Aktionen
laufen über die jeweiligen Phasen-Module (app/ermittlung, app/abmahnung, app/triage,
app/eskalation) — main.py enthält bewusst keine eigene Fachlogik.
"""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.abmahnung.generator import FallNichtBereitError, abmahnung_erzeugen
from app.database import get_fall, init_db, list_faelle
from app.eskalation.eskalation import NichtEskalierbarError, eskalierbar, eskalieren
from app.ermittlung.intake import neuen_fall_anlegen
from app.fristverwaltung.fristverwaltung import frist_abgelaufen
from app.models import GestattungsbeschlussStatus
from app.triage.klassifizierung import reaktion_registrieren

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Massenverfahren Case-Management (Prototyp)")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@app.on_event("startup")
def on_startup() -> None:
    init_db()


def _fall_or_404(fall_id: int):
    fall = get_fall(fall_id)
    if fall is None:
        raise HTTPException(status_code=404, detail=f"Fall {fall_id} nicht gefunden.")
    return fall


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    faelle = list_faelle()
    heute = date.today()
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "faelle": faelle,
            "heute": heute,
            "frist_abgelaufen": frist_abgelaufen,
            "eskalierbar": eskalierbar,
            "gestattungsbeschluss_status": list(GestattungsbeschlussStatus),
        },
    )


@app.get("/faelle/{fall_id}", response_class=HTMLResponse)
def fall_detail(request: Request, fall_id: int):
    fall = _fall_or_404(fall_id)
    return templates.TemplateResponse(
        "fall_detail.html",
        {"request": request, "fall": fall, "heute": date.today(), "eskalierbar": eskalierbar},
    )


@app.post("/faelle")
def fall_anlegen(
    ip_adresse: str = Form(...),
    werk: str = Form(...),
    mandant: str = Form(...),
    gestattungsbeschluss_status: str = Form(...),
    forderungshoehe_euro: float = Form(...),
):
    neuen_fall_anlegen(
        ip_adresse=ip_adresse,
        werk=werk,
        mandant=mandant,
        zeitstempel=datetime.utcnow(),
        gestattungsbeschluss_status=GestattungsbeschlussStatus(gestattungsbeschluss_status),
        forderungshoehe_euro=forderungshoehe_euro,
    )
    return RedirectResponse("/", status_code=303)


@app.post("/faelle/{fall_id}/abmahnung")
def fall_abmahnen(fall_id: int):
    fall = _fall_or_404(fall_id)
    try:
        abmahnung_erzeugen(fall)
    except FallNichtBereitError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return RedirectResponse(f"/faelle/{fall_id}", status_code=303)


@app.get("/faelle/{fall_id}/abmahnung", response_class=PlainTextResponse)
def abmahnung_anzeigen(fall_id: int):
    fall = _fall_or_404(fall_id)
    if not fall.abmahnung_pfad:
        raise HTTPException(status_code=404, detail="Für diesen Fall wurde noch keine Abmahnung erzeugt.")
    pfad = BASE_DIR.parent / fall.abmahnung_pfad
    return pfad.read_text(encoding="utf-8")


@app.post("/faelle/{fall_id}/reaktion")
def reaktion_erfassen(fall_id: int, reaktion_text: str = Form(...)):
    fall = _fall_or_404(fall_id)
    reaktion_registrieren(fall, reaktion_text)
    return RedirectResponse(f"/faelle/{fall_id}", status_code=303)


@app.post("/faelle/{fall_id}/eskalieren")
def fall_eskalieren(fall_id: int):
    fall = _fall_or_404(fall_id)
    try:
        eskalieren(fall)
    except NichtEskalierbarError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return RedirectResponse(f"/faelle/{fall_id}", status_code=303)
