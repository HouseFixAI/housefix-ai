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
        "steps": ["Maak de scheur voorzichtig breder met een plamuurmes", "Stofzuig losse deeltjes weg", "Vul de scheur met muurvuller en strijk glad", "Schuur licht op na droging", "Verf over met bijpassende muurverf"],
        "materials": ["Muurvuller (bijv. Alabastine)", "Plamuurmes", "Fijn schuurpapier (korrel 120)", "Muurverf", "Schilderstape", "Stofzuiger"],
        "cost_diy": "€15 - €35",
        "cost_pro": "€100 - €250"
    },
    {
        "issue_type": "lekkage loodgieter",
        "description": "Water dat lekt uit een pijpverbinding of kraan. Dit kan komen door een losse verbinding, versleten rubbers of pijpcorrosie die vervanging nodig heeft.",
        "cost_range": "€120 - €500",
        "confidence": "medium",
        "steps": ["Draai de waterhoofdkraan dicht", "Maak de verbinding los met een waterpomptang", "Vervang de rubberen ring of het aangetaste stuk pijp", "Draai alles weer vast en zet de watertoevoer open", "Controleer op lekkage met een droge doek"],
        "materials": ["Nieuwe rubberen ringen / O-ringen", "Waterpomptang", "Teflontape", "Emmer", "Droge doeken"],
        "cost_diy": "€10 - €25",
        "cost_pro": "€150 - €400"
    },
    {
        "issue_type": "verfbladderen",
        "description": "Verf die borrelt en bladdert van het muuroppervlak, vaak door vocht eronder of slechte voorbereiding van de ondergrond voor het schilderen.",
        "cost_range": "€80 - €400",
        "confidence": "high",
        "steps": ["Verwijder loszittende verf met een verfkrabber", "Schuur de randen glad", "Breng een voorstrijk/grondverf aan", "Plamuur oneffenheden bij", "Verf opnieuw met latexverf"],
        "materials": ["Verfkrabber", "Schuurpapier (korrel 80 en 120)", "Voorstrijk (grondverf)", "Plamuur", "Latexverf", "Schilderstape", "Verfroller en kwast"],
        "cost_diy": "€25 - €60",
        "cost_pro": "€200 - €500"
    },
    {
        "issue_type": "verstopte afvoer",
        "description": "Langzame of geblokkeerde afvoer in gootsteen, douche of toilet. Waarschijnlijk veroorzaakt door haar, vet of ophoping van vuil in de leiding.",
        "cost_range": "€60 - €280",
        "confidence": "high",
        "steps": ["Haal zichtbaar vuil uit de afvoer", "Giet een mengsel van baking soda en azijn in de afvoer", "Spoel na met kokend water", "Gebruik een ontstopper of veer als het hardnekkig is"],
        "materials": ["Baking soda (zuiveringszout)", "Natuurazijn", "Kokend water", "Ontstopper (plopper)", "Afvoerveer / ontstoppingsset (bijv. bij Praxis)", "Emmer"],
        "cost_diy": "€5 - €20",
        "cost_pro": "€100 - €250"
    },
    {
        "issue_type": "defect stopcontact",
        "description": "Het stopcontact werkt niet of valt uit. Dit kan een gesprongen zekering, losse bedrading of een defect stopcontact zijn dat vervangen moet worden.",
        "cost_range": "€80 - €200",
        "confidence": "medium",
        "steps": ["Schakel de stroom uit in de groepenkast", "Verwijder de afdekplaat van het stopcontact", "Controleer of draden goed vastzitten", "Vervang het stopcontact indien nodig", "Monteer de afdekplaat terug en zet de stroom weer aan"],
        "materials": ["Nieuw stopcontact (bijv. Gira of Jung)", "Spanningzoeker / multimeter", "Schroevendraaier set", "Striptang"],
        "cost_diy": "€10 - €25",
        "cost_pro": "€80 - €180"
    },
    {
        "issue_type": "gebroken raam",
        "description": "Een gebarsten of kapotte ruit. Vereist glasvervanging en professionele installatie voor een goede afdichting en veiligheid.",
        "cost_range": "€150 - €500",
        "confidence": "high",
        "steps": ["Verwijder voorzichtig glasresten met handschoenen", "Meet de opening nauwkeurig op", "Bestel een nieuwe ruit op maat (bijv. bij Karwei)", "Verwijder oude kit en plaats de nieuwe ruit", "Kit de ruit af en laat drogen"],
        "materials": ["Nieuwe ruit op maat", "Werkhandschoenen", "Kitpistool en glaskit", "Verfkrabber", "Messenblokjes voor afstand", "Glaslatten"],
        "cost_diy": "€30 - €80",
        "cost_pro": "€200 - €600"
    },
    {
        "issue_type": "overwoekerde tuin",
        "description": "Overmatige onkruidgroei, overwoekerde struiken of onverzorgd gazon dat gesnoeid, gewied en algemeen tuinonderhoud nodig heeft.",
        "cost_range": "€80 - €320",
        "confidence": "medium",
        "steps": ["Verwijder onkruid met de hand of een schoffel", "Snoei overwoekerde struiken en heggen", "Maai het gazon", "Hark bladeren en tuinafval bij elkaar", "Breng nieuwe tuinaarde of mulch aan"],
        "materials": ["Tuinhandschoenen", "Snoeischaar", "Heggenschaar (handmatig of elektrisch)", "Grasmaaier", "Hark", "Schoffel", "Tuinafvalzakken"],
        "cost_diy": "€15 - €50",
        "cost_pro": "€100 - €350"
    },
    {
        "issue_type": "houtrot",
        "description": "Aangetast of rottend hout op terras, schutting of raamkozijn door langdurige blootstelling aan vocht. Aangetaste delen moeten worden verwijderd en vervangen.",
        "cost_range": "€250 - €1,000",
        "confidence": "medium",
        "steps": ["Verwijder het rotte hout met een beitel of multitool", "Breng houtvuller aan voor kleine plekken of vervang het hele stuk", "Schuur glad na droging", "Breng een grondverf/houtimpregneer aan", "Verf of beits het hout"],
        "materials": ["Houtvuller (bijv. Bison Houtherstel)", "Beltel / Multitool", "Schuurpapier (korrel 60-120)", "Houtimpregneer", "Verf of beits (bijv. Sikkens)", "Kwasten en roller"],
        "cost_diy": "€20 - €60",
        "cost_pro": "€250 - €1,200"
    },
    {
        "issue_type": "gebarsten tegel",
        "description": "Gebroken of gebarsten keramische tegel op vloer of muur. Vereist verwijdering van de tegel, voorbereiding van de lijm en plaatsing van een nieuwe tegel.",
        "cost_range": "€120 - €400",
        "confidence": "high",
        "steps": ["Verwijder de oude tegel met een beitel en hamer", "Verwijder oude lijmresten", "Breng nieuwe tegellijm aan", "Plaats de nieuwe tegel en gebruik kruisjes voor gelijke voegen", "Voeg de tegel af met voegmiddel"],
        "materials": ["Nieuwe tegel (zelfde formaat)", "Hammer en beitel", "Tegellijm", "Tegelkruisjes", "Voegmiddel", "Spons en emmer"],
        "cost_diy": "€10 - €30",
        "cost_pro": "€120 - €350"
    },
    {
        "issue_type": "lekkende kraan",
        "description": "Een druppelende kraan die water verspilt, meestal veroorzaakt door een versleten rubbers, O-ring of patroon die vervangen moet worden.",
        "cost_range": "€60 - €160",
        "confidence": "high",
        "steps": ["Draai de watertoevoer naar de kraan dicht", "Verwijder de hendel van de kraan", "Vervang de rubberen ring of cartridge", "Zet de kraan weer in elkaar", "Open de watertoevoer en test of de kraan nog lekt"],
        "materials": ["Nieuwe rubberen ring / O-ring set", "Cartridge (passend bij merk kraan)", "Inbussleutel set", "Waterpomptang", "Schroevendraaier"],
        "cost_diy": "€8 - €20",
        "cost_pro": "€75 - €150"
    },
]

SYSTEM_PROMPT = (
    "You are a critical Dutch home repair expert. You analyze photos of home issues.\n\n"
    "CRITICAL SELF-CHECK - First: is there ACTUAL visible damage, wear, or a problem?\n"
    "• If the wall, floor, ceiling, surface, or object looks NORMAL, HEALTHY, and UNDAMAGED "
    "(even if old or weathered), then do NOT invent a problem. Return exactly this: "
    "{\"no_damage\": true, \"message\": \"✅ Geen schade geconstateerd. "
    "Deze muur/oppervlak ziet er constructief goed uit. Er is geen reparatie nodig.\"}\n"
    "• Only proceed if you can clearly see cracks, leaks, rot, peeling, stains, breakage, "
    "or other visible defects.\n\n"
    "CRITICAL RULE — If the image shows a CHAIR, TABLE, BED, SOFA, or any FURNITURE, "
    "or a CLEAN FLOOR without visible damage, you MUST return {\"no_damage\": true}. "
    "Do NOT invent 'verfbladderen' or 'scheur' or any damage on furniture or clean floors. "
    "Only real cracks, water damage, rot, or broken structures qualify as damage.\n\n"
    "SAFETY RULES - Check the image:\n"
    "1. If you see a person, face, animal, or pet, STOP and return exactly this: "
    "{\"error\": \"⚠️ HouseFix AI is speciaal ontworpen voor klussen, objecten en schade in of rondom het huis. Richt de camera alstublieft op het specifieke klusprobleem.\"}\n"
    "2. If the image clearly shows something completely unrelated to home repair (a car, food, landscape, phone screen, etc.), STOP and return exactly this: "
    "{\"error\": \"🔍 Dit object of deze situatie wordt niet herkend als een klusprobleem. Maak een nieuwe, duidelijke foto van de schade of het object.\"}\n\n"
    "UNCERTAIN - If you are not confident (less than 90% sure what the issue is), or the image shows a plain wall/floor/ceiling without visible damage, then do NOT guess. Instead return: "
    "{\"needs_clarification\": true, \"questions\": ["
    "{\"id\": \"size\", \"question\": \"📏 Hoe groot is het probleem ongeveer?\", \"options\": [\"Klein (pleisterformaat)\", \"Middel (handformaat)\", \"Groot (groter dan 50 cm)\"]},"
    "{\"id\": \"location\", \"question\": \"🏠 Is het binnen of buiten?\", \"options\": [\"Binnen\", \"Buiten\"]},"
    "{\"id\": \"water\", \"question\": \"💧 Komt er vocht/natte plekken bij kijken?\", \"options\": [\"Ja, het is nat\", \"Nee, het is droog\", \"Weet ik niet\"]},"
    "{\"id\": \"timing\", \"question\": \"⏰ Sinds wanneer speelt dit?\", \"options\": [\"Net ontdekt\", \"Enkele dagen\", \"Weken of langer\"]}"
    "]}\n\n"
    "ONLY if there is CLEAR, VISIBLE damage AND you are at least 90% confident, analyze it and return valid JSON with these keys:\n"
    "issue_type (short, precise label in Dutch, 1-3 words like 'scheur in muur'),\n"
    "description (1-2 concise sentences in Dutch explaining the problem and what causes it),\n"
    "steps (an array of 4-5 short, direct DIY repair steps in Dutch),\n"
    "materials (an array of specific materials/tools available at Gamma or Praxis),\n"
    "cost_diy (string like '€15 - €35' for materials only),\n"
    "cost_pro (string like '€100 - €250' for professional including travel costs),\n"
    "cost_range (string like '€50 - €250' overall range),\n"
    "confidence (high/medium/low).\n"
    "Always return ALL 8 fields for a full analysis. Be extremely precise with costs. "
    "BETTER TO RETURN 'no_damage' THAN TO INVENT A PROBLEM THAT DOESN'T EXIST."
)

INSPIRATION_PROMPT = (
    "You are a Dutch interior design and DIY inspiration expert. Look at the photo and describe what you see.\n\n"
    "ABSOLUTELY FORBIDDEN: You MUST NOT look for damage, cracks, leaks, rot, peeling paint, or repairs. "
    "This is an INSPIRATION mode. The user wants to know about style, not find problems.\n"
    "• Chairs, tables, sofas, beds, carpets, curtains, lamps are INTERIOR OBJECTS — not damage.\n"
    "• Clean concrete, brick, rough wood, worn surfaces are DESIGN CHOICES — not damage.\n"
    "• If you see a person, face, animal, or pet, STOP and return exactly this: "
    "{\"error\": \"⚠️ HouseFix AI Interieur kan geen gezichten of dieren analyseren. Richt op het interieur.\"}\n"
    "• If the image is completely unrelated (car, food, landscape, screen), STOP and return: "
    "{\"error\": \"🔍 Dit is niet herkend als interieur- of designfoto. Probeer een foto van een ruimte, meubel of materiaal.\"}\n\n"
    "If you are uncertain about what you see, return: "
    "{\"needs_clarification\": true, \"questions\": ["
    "{\"id\": \"room\", \"question\": \"🏠 Welke ruimte is dit?\", \"options\": [\"Woonkamer\", \"Slaapkamer\", \"Keuken\", \"Badkamer\", \"Entree/gang\"]},"
    "{\"id\": \"goal\", \"question\": \"🎯 Wat is je doel?\", \"options\": [\"Inspiratie opdoen\", \"Stijl benoemen\", \"Materiaal herkennen\", \"Zelf iets namaken\"]}"
    "]}\n\n"
    "OTHERWISE, return valid JSON with these keys:\n"
    "style (short description of the interior style in Dutch, e.g. 'Industrieel met Scandinavische invloeden'),\n"
    "description (2-3 sentences in Dutch describing materials, colors, textures, atmosphere),\n"
    "colors (an array of 3-5 dominant color names in Dutch),\n"
    "materials (an array of visible materials in Dutch),\n"
    "diy_tips (an array of 2-3 simple DIY inspiration ideas in Dutch),\n"
    "gamma_tips (an array of 2-3 specific products from Gamma/Praxis that match this style),\n"
    "confidence (high/medium/low).\n"
    "Always return ALL 7 fields. Be specific and helpful. Never mention damage, repair, or problems."
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
    """Accept a base64 image + mode, analyze with GPT-4o, return results."""
    import re as regex_module

    try:
        data = request.get_json()
    except Exception:
        return jsonify({"error": "Invalid JSON body"}), 400

    if not data or "image" not in data:
        return jsonify({"error": "No image provided"}), 400

    image_base64 = data["image"]
    mode = data.get("mode", "damage")  # "damage" or "inspiration"
    if not isinstance(image_base64, str) or len(image_base64) < 100:
        return jsonify({"error": "Invalid image data"}), 400

    # If no API key, return fallback
    if not OPENAI_API_KEY:
        return jsonify(random.choice(FALLBACK_ISSUES))

    # Choose the right prompt based on mode
    if mode == "inspiration":
        system_prompt = INSPIRATION_PROMPT
        user_text = "Analyze this interior/design photo and return the JSON as instructed."
    else:
        system_prompt = SYSTEM_PROMPT
        user_text = "Analyze this home repair issue and return the JSON as instructed."

    try:
        client = OpenAI(api_key=OPENAI_API_KEY)

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_text},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}},
                    ],
                },
            ],
            max_tokens=600,
            temperature=0.2,
        )

        message = response.choices[0].message.content
app.logger.info(f"RAW GPT RESPONSE:
{message}")
        # Extract JSON from response (may be wrapped in markdown)
        json_match = regex_module.search(r'\{.*\}', message, regex_module.DOTALL)
        if json_match:
            parsed = json.loads(json_match.group())
            # Check if GPT returned a safety error (person/animal/unrelated object)
            if isinstance(parsed, dict) and "error" in parsed:
                return jsonify({"warning": parsed["error"]})
            # Check if GPT says no damage visible (normal/healthy surface)
            if isinstance(parsed, dict) and parsed.get("no_damage"):
                return jsonify({"no_damage": True, "message": parsed.get("message", "✅ Geen schade geconstateerd.")})
            # Check if GPT needs clarification (uncertain about plain wall/floor)
            if isinstance(parsed, dict) and parsed.get("needs_clarification"):
                return jsonify({"needs_clarification": True, "questions": parsed.get("questions", [])})
            # Normal repair analysis
            if isinstance(parsed, dict) and "issue_type" in parsed:
                return jsonify(parsed)

        return jsonify(random.choice(FALLBACK_ISSUES))

    except Exception as e:
        app.logger.error(f"Analyze error: {e}")
        return jsonify({"error": str(e), "fallback": random.choice(FALLBACK_ISSUES)}), 500


@app.route("/api/analyze-with-context", methods=["POST"])
def analyze_with_context():
    """Second step: image + clarification answers → full analysis."""
    import re as regex_module

    try:
        data = request.get_json()
    except Exception:
        return jsonify({"error": "Invalid JSON body"}), 400

    if not data or "image" not in data or "answers" not in data:
        return jsonify({"error": "Missing image or answers"}), 400

    image_base64 = data["image"]
    answers = data["answers"]
    mode = data.get("mode", "damage")
    if not isinstance(image_base64, str) or len(image_base64) < 100:
        return jsonify({"error": "Invalid image data"}), 400

    if not OPENAI_API_KEY:
        return jsonify(random.choice(FALLBACK_ISSUES))

    # Build context string from answers
    context_lines = []
    for q in answers:
        context_lines.append(f"{q['question']} → {q['answer']}")
    user_context = "\n".join(context_lines)

    # Choose the right base prompt based on mode
    base_prompt = INSPIRATION_PROMPT if mode == "inspiration" else SYSTEM_PROMPT

    try:
        client = OpenAI(api_key=OPENAI_API_KEY)

        prompt_with_context = base_prompt + (
            f"\n\nThe user provided these details about their issue:\n{user_context}\n"
            "Now give your best, most accurate analysis based on the photo AND these details."
        )

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": prompt_with_context},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Analyze this home repair issue with the context provided."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}},
                    ],
                },
            ],
            max_tokens=500,
            temperature=0.2,
        )

        message = response.choices[0].message.content
        json_match = regex_module.search(r'\{.*\}', message, regex_module.DOTALL)
        if json_match:
            parsed = json.loads(json_match.group())
            if isinstance(parsed, dict) and "issue_type" in parsed:
                return jsonify(parsed)
app.logger.info("FALLBACK TRIGGERED")
        return jsonify(random.choice(FALLBACK_ISSUES))

    except Exception as e:
        app.logger.error(f"Analyze-with-context error: {e}")
        return jsonify({"error": str(e), "fallback": random.choice(FALLBACK_ISSUES)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
