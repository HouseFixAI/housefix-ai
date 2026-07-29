"""
AI-Telefoniste v2 — Bland.ai backend.
Eén endpoint: POST /api/tool — function calling voor Bland.ai.
Port 8000.
"""

import json
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from booking import get_availability, book_appointment, init_db
from config import BUSINESSES

init_db()

app = FastAPI(title="AI-Telefoniste v2 - Kapperszaken")


class ToolRequest(BaseModel):
    toolName: str
    arguments: dict


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
async def handle_tool(req: ToolRequest):
    """
    Bland.ai function calling endpoint.
    
    Bland stuurt een POST met:
    {
      "toolName": "check_availability" | "book_appointment",
      "arguments": {
        "business_id": "kapsalon-knal",
        "day_of_week": "thursday",
        "time": "14:00",           # alleen bij book_appointment
        "customer_name": "Sanne",  # alleen bij book_appointment
        "service": "knippen",      # alleen bij book_appointment
        "stylist": "Lisa"          # optioneel
      }
    }
    """
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
    uvicorn.run(app, host="0.0.0.0", port=8000)
