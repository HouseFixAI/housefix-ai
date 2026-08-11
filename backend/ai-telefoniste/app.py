"""
AI-Telefoniste v2 — Bland.ai backend.
Eén endpoint: POST /api/tool — function calling voor Bland.ai.
Bindt op 127.0.0.1 (loopback) — alleen bereikbaar via de HouseFix-proxy,
die de gedeelde API-key verifieert en doorstuurt als X-Internal-Key.
"""

import hmac
import json
import os
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from booking import get_availability, book_appointment, init_db
from config import BUSINESSES

# Load .env (simple loader; does not override existing env vars)
_env_path = Path(__file__).parent / ".env"
if _env_path.exists():
    for _line in _env_path.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _, _v = _line.partition("=")
            _k, _v = _k.strip(), _v.strip().strip("\"'")
            if _k and _k not in os.environ:
                os.environ[_k] = _v

TELEFONISTE_API_KEY = os.environ.get("TELEFONISTE_API_KEY", "")

init_db()

app = FastAPI(title="AI-Telefoniste v2 - Kapperszaken")


class ToolRequest(BaseModel):
    toolName: str
    arguments: dict


def _check_key(request: Request) -> bool:
    """Accept X-Internal-Key (from HouseFix proxy) or X-Api-Key (direct)."""
    key = request.headers.get("X-Internal-Key") or request.headers.get("X-Api-Key") or ""
    return bool(TELEFONISTE_API_KEY) and hmac.compare_digest(key, TELEFONISTE_API_KEY)


@app.get("/")
def home():
    """Health check + overzicht"""
    return {
        "service": "AI-Telefoniste v2 (Bland.ai backend)",
        "businesses": len(BUSINESSES),
        "names": [b["name"] for b in BUSINESSES.values()],
        "endpoints": {
            "POST /api/tool": "Function calling endpoint voor Bland.ai",
            "GET /api/businesses": "Lijst van alle gekoppelde zaken",
            "GET /api/businesses/{id}": "Detail van één zaak",
        },
    }


@app.get("/api/health")
def health():
    return {"status": "ok", "businesses": len(BUSINESSES)}


@app.get("/api/businesses")
def list_businesses():
    """Lijst alle beschikbare kapperszaken."""
    return [
        {
            "id": bid,
            "name": b["name"],
            "address": b["address"],
            "phone": b["phone"],
            "services": b["services"],
            "stylists": b["stylists"],
        }
        for bid, b in BUSINESSES.items()
    ]


@app.get("/api/businesses/{business_id}")
def get_business_detail(business_id: str):
    """Detail van één zaak."""
    b = BUSINESSES.get(business_id)
    if not b:
        return JSONResponse({"error": f"Onbekende zaak: {business_id}"}, status_code=404)
    return {
        "id": business_id,
        "name": b["name"],
        "address": b["address"],
        "phone": b["phone"],
        "ai_name": b["ai_name"],
        "owner": b["owner"],
        "services": b["services"],
        "stylists": b["stylists"],
        "opening_hours": {k: v for k, v in b["opening_hours"].items() if v},
    }


@app.post("/api/tool")
async def handle_tool(request: Request, req: ToolRequest):
    """
    Bland.ai function calling endpoint. Requireert de gedeelde API-key
    (X-Internal-Key via de HouseFix-proxy, of X-Api-Key direct).
    """
    if not _check_key(request):
        return JSONResponse({"error": "Ongeldige API-key"}, status_code=401)

    tool_name = req.toolName
    args = req.arguments

    business_id = args.get("business_id", "")
    if business_id not in BUSINESSES:
        return {"error": f"Onbekende zaak. Kies uit: {', '.join(BUSINESSES.keys())}"}

    if tool_name == "check_availability":
        day = args.get("day_of_week", "").lower().strip()
        if not day:
            return {"error": "Geen dag opgegeven. Gebruik day_of_week: monday, tuesday, etc."}
        valid_days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        if day not in valid_days:
            return {"error": f"Ongeldige dag. Kies uit: {', '.join(valid_days)}"}
        return get_availability(business_id, day)

    elif tool_name == "book_appointment":
        required = ["day_of_week", "time", "customer_name", "service"]
        missing = [f for f in required if f not in args or not args[f]]
        if missing:
            return {"error": f"Ontbrekende velden: {', '.join(missing)}"}

        return book_appointment(
            business_id=business_id,
            day_of_week=args["day_of_week"],
            time_str=args["time"],
            customer_name=args["customer_name"],
            service=args["service"],
            customer_phone=args.get("customer_phone", ""),
            stylist=args.get("stylist", ""),
        )

    else:
        return {"error": f"Onbekende tool: {tool_name}. Gebruik check_availability of book_appointment."}


if __name__ == "__main__":
    import uvicorn
    # Loopback only: publiek bereikbaar via de HouseFix-proxy op port 3000,
    # die de API-key verifieert. Nooit direct op 0.0.0.0 zetten.
    uvicorn.run(app, host="127.0.0.1", port=8001)
