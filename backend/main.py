"""
HouseFix AI — FastAPI Backend

Endpoints:
  POST /api/analyze   — Accept image, analyze with AI vision model, return issue details + cost estimate
  GET  /api/providers — Return seeded list of local service providers
  GET  /api/health    — Health check
"""

import json
import os
import random
import uuid
from pathlib import Path

import httpx
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

# ---------------------------------------------------------------------------
# Paths & Config
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
PROVIDERS_PATH = BASE_DIR / "providers.json"
STATIC_DIR = BASE_DIR / "static"

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
VISION_API_URL = os.environ.get("VISION_API_URL", "https://api.openai.com/v1/chat/completions")

# ---------------------------------------------------------------------------
# Providers data (loaded once at import time)
# ---------------------------------------------------------------------------
with open(PROVIDERS_PATH) as f:
    PROVIDERS = json.load(f)

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(title="HouseFix AI", version="1.0.0")

# CORS — allow all origins for MVP
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static frontend build at /static/ path
_static_files = list(STATIC_DIR.iterdir()) if STATIC_DIR.is_dir() else []
if _static_files:
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")


# ---------------------------------------------------------------------------
# Catch-all route for SPA frontend
# ---------------------------------------------------------------------------
@app.get("/")
async def serve_frontend():
    index = STATIC_DIR / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return {"message": "HouseFix AI backend is running. Frontend build not found."}


# ---------------------------------------------------------------------------
# Mock / fallback analysis (used when no vision API URL is configured)
# ---------------------------------------------------------------------------
FALLBACK_ISSUES = [
    {
        "issue_type": "scheur in muur",
        "description": "Een zichtbare scheur in de gipsmuur, waarschijnlijk veroorzaakt door verzakking of kleine structurele beweging. Meestal oppervlakkig en te repareren met plamuur en verf.",
        "cost_range": "€50 - €150",
        "confidence": "medium",
    },
    {
        "issue_type": "lekkage loodgieter",
        "description": "Water dat lekt uit een pijpverbinding of kraan. Dit kan komen door een losse verbinding, versleten rubbers of pijpcorrosie die vervanging nodig heeft.",
        "cost_range": "€120 - €500",
        "confidence": "medium",
    },
    {
        "issue_type": "verfbladderen",
        "description": "Verf die borrelt en bladdert van het muuroppervlak, vaak door vocht eronder of slechte voorbereiding van de ondergrond voor het schilderen.",
        "cost_range": "€80 - €400",
        "confidence": "high",
    },
    {
        "issue_type": "verstopte afvoer",
        "description": "Langzame of geblokkeerde afvoer in gootsteen, douche of toilet. Waarschijnlijk veroorzaakt door haar, vet of ophoping van vuil in de leiding.",
        "cost_range": "€60 - €280",
        "confidence": "high",
    },
    {
        "issue_type": "defect stopcontact",
        "description": "Het stopcontact werkt niet of valt uit. Dit kan een gesprongen zekering, losse bedrading of een defect stopcontact zijn dat vervangen moet worden.",
        "cost_range": "€80 - €200",
        "confidence": "medium",
    },
    {
        "issue_type": "gebroken raam",
        "description": "Een gebarsten of kapotte ruit. Vereist glasvervanging en professionele installatie voor een goede afdichting en veiligheid.",
        "cost_range": "€150 - €500",
        "confidence": "high",
    },
    {
        "issue_type": "overwoekerde tuin",
        "description": "Overmatige onkruidgroei, overwoekerde struiken of onverzorgd gazon dat gesnoeid, gewied en algemeen tuinonderhoud nodig heeft.",
        "cost_range": "€80 - €320",
        "confidence": "medium",
    },
    {
        "issue_type": "houtrot",
        "description": "Aangetast of rottend hout op terras, schutting of raamkozijn door langdurige blootstelling aan vocht. Aangetaste delen moeten worden verwijderd en vervangen.",
        "cost_range": "€250 - €1,000",
        "confidence": "medium",
    },
    {
        "issue_type": "gebarsten tegel",
        "description": "Gebroken of gebarsten keramische tegel op vloer of muur. Vereist verwijdering van de tegel, voorbereiding van de lijm en plaatsing van een nieuwe tegel.",
        "cost_range": "€120 - €400",
        "confidence": "high",
    },
    {
        "issue_type": "lekkende kraan",
        "description": "Een druppelende kraan die water verspilt, meestal veroorzaakt door een versleten rubbers, O-ring of patroon die vervangen moet worden.",
        "cost_range": "€60 - €160",
        "confidence": "high",
    },
]


def _fallback_analysis() -> dict:
    """Return a random fallback analysis when no real AI API is configured."""
    return random.choice(FALLBACK_ISSUES)


async def _ai_analysis(image_bytes: bytes, content_type: str) -> dict:
    """Call the external vision AI API for image analysis.

    Sends the prompt as a system message and the image as a user message
    using the OpenAI-compatible chat completions format (works with OpenAI,
    Gemini via OpenAI-compatible endpoint, Claude, etc.).

    Falls back to mock data if VISION_API_URL is not set or the call fails.
    """
    if not OPENAI_API_KEY:
        return _fallback_analysis()

    try:
        system_prompt = (
            "You are a Dutch home repair expert. Examine this image of a home issue. "
            "Identify the problem, explain it in clear Dutch, and give a highly accurate "
            "cost estimate in Euros (€) for hiring a professional in the Netherlands. "
            "Keep the price range tight (maximum 30% margin between low and high estimate). "
            "Respond in valid JSON with exactly these keys: "
            "issue_type (short label), description (2-3 sentence explanation), "
            "cost_range (string like €150 - €200), confidence (high/medium/low)."
        )

        # Encode image as base64 for the API request
        import base64
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")
        data_uri = f"data:{content_type};base64,{image_base64}"

        request_body = {
            "model": os.environ.get("VISION_MODEL", "gpt-4o"),
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Analyze this home repair issue and return the JSON response as instructed.",
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": data_uri},
                        },
                    ],
                },
            ],
            "max_tokens": 500,
            "temperature": 0.2,
        }

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                VISION_API_URL,
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json=request_body,
            )
            resp.raise_for_status()
            data = resp.json()

        # Parse OpenAI-compatible response
        choices = data.get("choices", [])
        if choices:
            message = choices[0].get("message", {}).get("content", "")
            if message:
                # Try to extract JSON from the response (may be wrapped in markdown)
                import re
                json_match = re.search(r'\{.*\}', message, re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group())
                    if isinstance(parsed, dict) and "issue_type" in parsed:
                        return parsed

        # If we couldn't parse, fall back
        return _fallback_analysis()

    except Exception:
        return _fallback_analysis()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "HouseFix AI"}


@app.get("/api/providers")
async def list_providers(
    category: str | None = None,
    city: str | None = None,
):
    """Return seeded provider list, optionally filtered by category and/or city."""
    results = PROVIDERS
    if category:
        results = [p for p in results if p["category"].lower() == category.lower()]
    if city:
        results = [p for p in results if p["city"].lower() == city.lower()]
    return results


@app.post("/api/analyze")
async def analyze_image(file: UploadFile = File(...)):
    """Accept an image upload, analyze it with AI, return issue details."""
    # Validate file is an image
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="Only image files are supported (JPEG, PNG, GIF, WebP, etc.)",
        )

    # Read file bytes
    image_bytes = await file.read()

    # Size cap at 10 MB
    if len(image_bytes) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="Image too large. Maximum size is 10 MB.",
        )

    # Run analysis
    result = await _ai_analysis(image_bytes, file.content_type)

    return {
        "issue_type": result["issue_type"],
        "description": result["description"],
        "cost_range": result["cost_range"],
        "confidence": result["confidence"],
    }
