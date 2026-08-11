"""
Yard Management System — FastAPI Backend.
Pure FastAPI + Jinja2 templates.
"""

from datetime import datetime
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from pathlib import Path

from config import DCS, INSTRUCTIONS, DEFAULT_DOCKS, VALID_TRANSITIONS
from models import (
    init_db, is_plate_blocked, create_driver, get_driver_by_ticket,
    update_driver_status, move_position_back, increment_no_show,
    complete_driver, get_dc_dashboard, call_next_driver,
    reorder_queue, get_blocked_plates, unblock_plate,
    get_standby_count, get_connection, dict_from_row,
)
from state_machine import (
    validate_transition, InvalidTransitionError, BusinessRuleError,
    is_terminal, should_early_call, get_call_next_strategy,
)

app = FastAPI(title="Yard Management System")

# Jinja2 templates
TEMPLATES_DIR = Path(__file__).parent / "templates"
TEMPLATES_DIR.mkdir(exist_ok=True)
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


# ─── Pydantic models ─────────────────────────────────────────────

class CheckinRequest(BaseModel):
    name: str
    license_plate: str
    transporter: str
    cmr: str
    phone: str = ""
    dc_id: str = "dc-rotterdam"


class ConfirmRequest(BaseModel):
    pass  # no extra body needed


class PriorityUpdateRequest(BaseModel):
    ticket_ids: list[str]


# ─── Lifecycle ───────────────────────────────────────────────────

@app.on_event("startup")
def startup():
    init_db()


# ─── Frontend (Jinja2) ───────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request, "dc_id": "dc-rotterdam"})


@app.get("/dashboard/{dc_id}", response_class=HTMLResponse)
def dashboard_view(request: Request, dc_id: str):
    return templates.TemplateResponse("dashboard.html", {"request": request, "dc_id": dc_id})


# ─── Driver API ──────────────────────────────────────────────────

@app.post("/api/checkin")
def checkin(req: CheckinRequest):
    """Driver checks in. Returns ticket_id + position. Validates blocked plates."""
    plate = req.license_plate.upper()

    if is_plate_blocked(plate):
        raise HTTPException(
            status_code=403,
            detail="Uw kenteken is geblokkeerd. Neem contact op met de expediteur."
        )

    if req.dc_id not in DCS:
        raise HTTPException(status_code=404, detail="Distributiecentrum niet gevonden")

    driver = create_driver(
        dc_id=req.dc_id,
        name=req.name,
        license_plate=plate,
        transporter=req.transporter,
        cmr=req.cmr,
        phone=req.phone,
    )

    dc_config = DCS[req.dc_id]
    instructions = {}
    for lang in ["NL", "EN", "PL", "RO"]:
        tmpl = INSTRUCTIONS["Ingecheckt"].get(lang, "")
        instructions[lang] = tmpl.format(position=driver["position"])

    return {
        **driver,
        "instructions": instructions,
        "dc_name": dc_config["name"],
    }


@app.get("/api/status/{ticket_id}")
def get_status(ticket_id: str):
    """Returns current status, position, dock info, parking info, and instructions in 4 langs."""
    driver = get_driver_by_ticket(ticket_id)
    if not driver:
        raise HTTPException(status_code=404, detail="Ticket niet gevonden")

    dc_id = driver["dc_id"]
    dc_config = DCS.get(dc_id, {})
    status = driver["status"]

    # Build instructions in 4 languages
    instructions = {}
    tmpl_map = INSTRUCTIONS.get(status, {})
    for lang in ["NL", "EN", "PL", "RO"]:
        tmpl = tmpl_map.get(lang, "")
        formatted = tmpl.format(
            position=driver.get("position_in_queue", "?"),
            minutes=dc_config.get("reistijd_minuten", "?"),
            dock=driver.get("dock_id", "?"),
            count=driver.get("no_show_count", 0),
            limit=dc_config.get("no_show_limiet", "?"),
            hours=dc_config.get("blokkade_uren", "?"),
        )
        instructions[lang] = formatted

    dock_info = None
    if driver.get("dock_id"):
        conn = get_connection()
        try:
            dock = dict_from_row(conn.execute(
                "SELECT * FROM docks WHERE id = ?", (driver["dock_id"],)
            ).fetchone())
            if dock:
                dock_info = {"id": dock["id"], "name": dock["name"]}
        finally:
            conn.close()

    return {
        "ticket_id": driver["ticket_id"],
        "status": status,
        "position": driver.get("position_in_queue"),
        "dc_id": dc_id,
        "dc_name": dc_config.get("name", ""),
        "dock": dock_info,
        "instructions": instructions,
        "allowed_transitions": VALID_TRANSITIONS.get(status, []),
        "is_terminal": is_terminal(status),
        "status_updated_at": driver.get("status_updated_at"),
    }


@app.post("/api/confirm/{ticket_id}/onderweg")
def confirm_onderweg(ticket_id: str):
    """Driver confirms they are driving to standby."""
    driver = get_driver_by_ticket(ticket_id)
    if not driver:
        raise HTTPException(status_code=404, detail="Ticket niet gevonden")

    if driver["status"] != "Standby_Onderweg":
        raise HTTPException(status_code=400, detail=f"Ongeldige status: {driver['status']}")

    updated = update_driver_status(ticket_id, "Standby_Aangekomen")
    if not updated:
        raise HTTPException(status_code=500, detail="Fout bij updaten status")

    return {"status": "Standby_Aangekomen", "ticket_id": ticket_id}


@app.post("/api/confirm/{ticket_id}/aangekomen")
def confirm_aangekomen(ticket_id: str):
    """Driver confirms arrival at standby spot."""
    driver = get_driver_by_ticket(ticket_id)
    if not driver:
        raise HTTPException(status_code=404, detail="Ticket niet gevonden")

    if driver["status"] != "Standby_Aangekomen":
        raise HTTPException(status_code=400, detail=f"Ongeldige status: {driver['status']}")

    # Driver arrived at standby — they're ready to be called to dock
    return {
        "status": "Standby_Aangekomen",
        "ticket_id": ticket_id,
        "message": "U bent aangemeld op de standby-plek. Wacht tot een dok vrijkomt.",
    }


@app.post("/api/cannot/{ticket_id}")
def driver_cannot(ticket_id: str):
    """Driver refuses — moves 1 position back in queue."""
    driver = get_driver_by_ticket(ticket_id)
    if not driver:
        raise HTTPException(status_code=404, detail="Ticket niet gevonden")

    updated = move_position_back(ticket_id)
    if not updated:
        raise HTTPException(status_code=500, detail="Fout bij verplaatsen")

    return {
        "status": updated["status"],
        "position": updated["position_in_queue"],
        "ticket_id": ticket_id,
    }


# ─── Dashboard API ───────────────────────────────────────────────

@app.get("/api/dashboard/{dc_id}")
def dashboard(dc_id: str):
    """Full dashboard: all docks, all drivers by status, ordered by position."""
    data = get_dc_dashboard(dc_id)
    if "error" in data:
        raise HTTPException(status_code=404, detail=data["error"])

    # Count by status
    status_counts = {}
    for d in data["drivers"]:
        s = d["status"]
        status_counts[s] = status_counts.get(s, 0) + 1

    standby_count = get_standby_count(dc_id)
    dock_count = len(data["docks"])
    active_dock_count = sum(1 for d in data["drivers"] if d["status"] == "Actief_Dok")

    return {
        **data,
        "status_counts": status_counts,
        "standby_count": standby_count,
        "standby_slots": data["dc"]["standby_slots"],
        "dock_count": dock_count,
        "active_dock_count": active_dock_count,
    }


@app.post("/api/dashboard/{dc_id}/call-next")
def dashboard_call_next(dc_id: str):
    """Call next waiting driver to standby (or to dock if standby full)."""
    if dc_id not in DCS:
        raise HTTPException(status_code=404, detail="DC niet gevonden")

    result = call_next_driver(dc_id)
    if not result:
        return {"called": False, "message": "Geen wachtende chauffeurs"}

    return {
        "called": True,
        "driver": result,
        "ticket_id": result["ticket_id"],
        "new_status": result["status"],
        "message": f"Chauffeur {result.get('name')} opgeroepen naar {result['status']}",
    }


@app.post("/api/dashboard/{dc_id}/mark-complete/{ticket_id}")
def dashboard_mark_complete(dc_id: str, ticket_id: str):
    """Mark driver as completed."""
    driver = get_driver_by_ticket(ticket_id)
    if not driver:
        raise HTTPException(status_code=404, detail="Ticket niet gevonden")
    if driver["dc_id"] != dc_id:
        raise HTTPException(status_code=400, detail="Driver hoort niet bij dit DC")

    result = complete_driver(ticket_id)
    if not result:
        raise HTTPException(status_code=500, detail="Fout bij voltooien")

    return {"status": "Voltooid", "ticket_id": ticket_id}


@app.post("/api/dashboard/{dc_id}/mark-noshow/{ticket_id}")
def dashboard_mark_noshow(dc_id: str, ticket_id: str):
    """Mark driver as no-show. Increments counter, blocks if >= limit."""
    driver = get_driver_by_ticket(ticket_id)
    if not driver:
        raise HTTPException(status_code=404, detail="Ticket niet gevonden")
    if driver["dc_id"] != dc_id:
        raise HTTPException(status_code=400, detail="Driver hoort niet bij dit DC")

    result = increment_no_show(ticket_id)
    if not result:
        raise HTTPException(status_code=500, detail="Fout bij no-show verwerking")

    return {
        "ticket_id": ticket_id,
        "status": result["status"],
        "no_show_count": result["no_show_count"],
        "blocked": result["status"] == "Geblokkeerd",
    }


@app.post("/api/dashboard/{dc_id}/update-priority")
def dashboard_update_priority(dc_id: str, req: PriorityUpdateRequest):
    """Reorder queue — accepts array of ticket_ids in new order."""
    result = reorder_queue(dc_id, req.ticket_ids)
    return result


@app.get("/api/dashboard/{dc_id}/blocked")
def dashboard_blocked(dc_id: str):
    """List blocked plates."""
    plates = get_blocked_plates(dc_id)
    return {"dc_id": dc_id, "blocked": plates}


@app.post("/api/dashboard/{dc_id}/unblock/{plate}")
def dashboard_unblock(dc_id: str, plate: str):
    """Manually unblock a license plate."""
    result = unblock_plate(plate)
    return result


# ─── Health ──────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {"status": "ok", "service": "Yard Management System", "dcs": list(DCS.keys())}


# ─── Error handlers ──────────────────────────────────────────────

@app.exception_handler(InvalidTransitionError)
def handle_invalid_transition(request: Request, exc: InvalidTransitionError):
    return JSONResponse(status_code=400, content={"error": str(exc)})


@app.exception_handler(BusinessRuleError)
def handle_business_rule(request: Request, exc: BusinessRuleError):
    return JSONResponse(status_code=422, content={"error": str(exc)})


# ─── Run ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
