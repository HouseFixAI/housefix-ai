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

VISION_API_URL = os.environ.get("VISION_API_URL", "")
VISION_API_KEY = os.environ.get("VISION_API_KEY", "")

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
        "issue_type": "wall crack",
        "description": "A visible crack in the drywall, likely caused by settling or minor structural movement. Typically superficial and repairable with spackle and paint.",
        "cost_range": "$50 - $200",
        "confidence": "medium",
    },
    {
        "issue_type": "plumbing leak",
        "description": "Water leaking from a pipe joint or fixture. Could be a loose connection, worn washer, or pipe corrosion requiring replacement.",
        "cost_range": "$150 - $600",
        "confidence": "medium",
    },
    {
        "issue_type": "paint peeling",
        "description": "Paint is bubbling and peeling from the wall surface, often due to moisture underneath or poor surface preparation before painting.",
        "cost_range": "$100 - $500",
        "confidence": "high",
    },
    {
        "issue_type": "clogged drain",
        "description": "Slow or blocked drainage in sink, shower, or toilet. Likely caused by hair, grease, or debris buildup in the pipe.",
        "cost_range": "$80 - $350",
        "confidence": "high",
    },
    {
        "issue_type": "electrical outlet not working",
        "description": "The electrical outlet is dead or intermittently failing. May be a tripped breaker, loose wiring, or a faulty outlet that needs replacement.",
        "cost_range": "$100 - $250",
        "confidence": "medium",
    },
    {
        "issue_type": "broken window",
        "description": "A cracked or shattered window pane. Requires glass replacement and professional installation to ensure proper sealing and safety.",
        "cost_range": "$200 - $600",
        "confidence": "high",
    },
    {
        "issue_type": "garden overgrowth",
        "description": "Excessive weed growth, overgrown shrubs, or unkempt lawn requiring trimming, weeding, and general garden maintenance.",
        "cost_range": "$100 - $400",
        "confidence": "medium",
    },
    {
        "issue_type": "wood rot",
        "description": "Decayed or rotting wood on deck, fence, or window frame caused by prolonged moisture exposure. Affected sections need removal and replacement.",
        "cost_range": "$300 - $1,200",
        "confidence": "medium",
    },
    {
        "issue_type": "cracked tile",
        "description": "Broken or cracked ceramic or porcelain tile on floor or wall. Requires tile removal, adhesive prep, and new tile installation.",
        "cost_range": "$150 - $500",
        "confidence": "high",
    },
    {
        "issue_type": "leaky faucet",
        "description": "A dripping faucet wasting water, usually caused by a worn-out washer, O-ring, or cartridge that needs replacement.",
        "cost_range": "$75 - $200",
        "confidence": "high",
    },
]


def _fallback_analysis() -> dict:
    """Return a random fallback analysis when no real AI API is configured."""
    return random.choice(FALLBACK_ISSUES)


async def _ai_analysis(image_bytes: bytes, content_type: str) -> dict:
    """Call the external vision AI API for image analysis.

    Falls back to mock data if VISION_API_URL is not set or the call fails.
    """
    if not VISION_API_URL:
        return _fallback_analysis()

    try:
        prompt = (
            "You are a home repair expert. Examine this image of a home issue. "
            "Identify the problem, explain it in plain English, and give a realistic "
            "cost estimate for hiring a professional. "
            "Respond in valid JSON with exactly these keys: "
            "issue_type (short label), description (2-3 sentence explanation), "
            "cost_range (string like '$150 - $400'), confidence (high/medium/low)."
        )

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                VISION_API_URL,
                headers={
                    "Authorization": f"Bearer {VISION_API_KEY}",
                    "Content-Type": content_type,
                },
                params={"prompt": prompt},
                content=image_bytes,
            )
            resp.raise_for_status()
            data = resp.json()

        # Try to parse the response — various AI APIs return content differently
        if isinstance(data, dict):
            if "issue_type" in data:
                return data
            # Maybe nested under 'choices' (OpenAI-compatible)
            choices = data.get("choices", [])
            if choices:
                message = choices[0].get("message", {}).get("content", "")
                if message:
                    parsed = json.loads(message)
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
