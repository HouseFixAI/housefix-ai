from flask import Flask, render_template, request, jsonify
import os
import json
import random
from openai import OpenAI

app = Flask(__name__)

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

# ---------------------------------------------------------------------------
# Fallback data (used when no API key is configured)
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

SYSTEM_PROMPT = (
    "You are a Dutch home repair expert. Examine this image of a home issue. "
    "Identify the problem, explain it in clear Dutch, and give a highly accurate "
    "cost estimate in Euros (€) for hiring a professional in the Netherlands. "
    "Keep the price range tight (maximum 30% margin between low and high estimate). "
    "Respond in valid JSON with exactly these keys: "
    "issue_type (short label), description (2-3 sentence explanation), "
    "cost_range (string like €150 - €200), confidence (high/medium/low)."
)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "service": "HouseFix AI"})


@app.route("/api/providers")
def list_providers():
    """Return seeded provider list."""
    with open(os.path.join(os.path.dirname(__file__), "providers.json")) as f:
        providers = json.load(f)
    category = request.args.get("category")
    city = request.args.get("city")
    if category:
        providers = [p for p in providers if p["category"].lower() == category.lower()]
    if city:
        providers = [p for p in providers if p["city"].lower() == city.lower()]
    return jsonify(providers)


@app.route("/api/analyze", methods=["POST"])
def analyze_image():
    """Accept a base64 image, analyze with GPT-4o, return issue details."""
    import re as regex_module

    try:
        data = request.get_json()
    except Exception:
        return jsonify({"error": "Invalid JSON body"}), 400

    if not data or "image" not in data:
        return jsonify({"error": "No image provided"}), 400

    image_base64 = data["image"]
    if not isinstance(image_base64, str) or len(image_base64) < 100:
        return jsonify({"error": "Invalid image data"}), 400

    # If no API key, return fallback
    if not OPENAI_API_KEY:
        return jsonify(random.choice(FALLBACK_ISSUES))

    try:
        client = OpenAI(api_key=OPENAI_API_KEY)

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Analyze this home repair issue and return the JSON response as instructed.",
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"},
                        },
                    ],
                },
            ],
            max_tokens=500,
            temperature=0.2,
        )

        message = response.choices[0].message.content

        # Extract JSON from response (may be wrapped in markdown)
        json_match = regex_module.search(r'\{.*\}', message, regex_module.DOTALL)
        if json_match:
            parsed = json.loads(json_match.group())
            if isinstance(parsed, dict) and "issue_type" in parsed:
                return jsonify(parsed)

        return jsonify(random.choice(FALLBACK_ISSUES))

    except Exception as e:
        app.logger.error(f"Analyze error: {e}")
        return jsonify({"error": str(e), "fallback": random.choice(FALLBACK_ISSUES)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)