from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import json
import random
import uuid
import time
from openai import OpenAI

app = Flask(__name__)

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

# Serve static files (PWA manifest, icons, service worker)
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(os.path.join(os.path.dirname(__file__), 'static'), filename)

# ---------------------------------------------------------------------------
# Fallback data (used when no API key is configured)
# ---------------------------------------------------------------------------
FALLBACK_ISSUES = [
    {
        "issue_type": "scheur in muur",
        "building_element": "muur",
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
        "building_element": "leiding",
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
        "building_element": "muur",
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
        "building_element": "leiding",
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
        "building_element": "muur",
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
        "building_element": "kozijn",
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
        "building_element": "tuin",
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
        "building_element": "kozijn",
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
        "building_element": "vloer",
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
        "building_element": "leiding",
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
    "You are a helpful Dutch home repair assistant. Homeowners send you photos of "
    "issues they've noticed around their home. Your job is to tell them what they're "
    "looking at, what it means for their home, and what to do about it. "
    "The photo is your starting point — the homeowner is who you're helping.\n\n"
    "STRUCTURED APPROACH — First identify WHAT you are looking at, THEN check for damage:\n"
    "• STEP 1: Determine the building element in the photo. "
    "Is it a wall, ceiling, floor, roof, window/door frame, pipe/installation, tile work, "
    "or something else (garden, furniture, etc.)? Be specific.\n"
    "• STEP 2: Only within that building element context, check if there is ACTUAL visible "
    "damage, wear, or a problem. For example, 'plafond' has different problems than 'vloer' "
    "or 'leiding'. Roof issues involve leaks, wall issues involve cracks, pipe issues involve "
    "leaks or blockages.\n\n"
    "IDENTIFICATION GUIDE — Use these visual clues to identify the building element:\n"
    "• muur/wall: vertical orientation, light switches/outlets, baseboards, artwork/windows\n"
    "• plafond/ceiling: seen from below, light fixtures/fans, corners where walls meet, no baseboards\n"
    "• vloer/floor: seen from above, furniture legs/feet on it, baseboards at edges, floor tiles/planks\n"
    "• dak/roof: sloped, outdoor, tiles/shingles, sky background visible\n"
    "• kozijn/frame: rectangular border, hinges, glass or door inside, sealant/kit lines\n"
    "• leiding/pipe: cylindrical, metal or white PVC, angled joints, faucet/drain attached\n"
    "• tegelwerk/tile: small repeating units, grout lines, often on wall or floor\n"
    "• tuin/garden: plants, soil, grass, outdoor context, no building surface\n\n"
    "CRITICAL SELF-CHECK - First: is there ACTUAL visible damage, wear, maintenance need, or a problem?\n"
    "• If the wall, floor, ceiling, surface, or object looks COMPLETELY NEW, CLEAN, and FREE "
    "OF ANY ISSUES, then do NOT invent a problem. Return exactly this: "
    "{\"no_damage\": true, \"message\": \"✅ Geen problemen geconstateerd. "
    "Dit oppervlak of object ziet er goed uit. Er is geen onderhoud of reparatie nodig.\"}\n"
    "• HOWEVER, if you see ANY of the following issues, DO report them: cracks, leaks, rot, "
    "peeling paint, stains, breakage, holes, dents, moss, algae, green growth, mold, mildew, "
    "dirt/soiling, weathering/oxidation (grey/silvered wood), wear, fading, discoloration, "
    "loose material, rust, efflorescence (white salt deposits), or any visible issue that "
    "would benefit from cleaning, treatment, maintenance, or repair.\n"
    "• Age alone is NOT a reason to call something 'no_damage'. If an old surface shows "
    "signs of weathering, wear, moss, algae, or soiling that a homeowner would want to "
    "address, report it. HouseFix AI is a HOME ASSISTANT that helps with all home issues: "
    "repair, maintenance, cleaning, and treatment.\n\n"
    "CRITICAL RULE — If the image shows a CHAIR, TABLE, BED, SOFA, or any FURNITURE, "
    "or a CLEAN FLOOR without visible damage, you MUST return {\"no_damage\": true}. "
    "Do NOT invent 'verfbladderen' or 'scheur' or any damage on furniture or clean floors. "
    "Issues like dirt, wear, scratches, or stains on furniture CAN be reported if clearly visible. "
    "Only report what you actually see — do not exaggerate or invent.\n\n"
    "SAFETY RULES - Check the image:\n"
    "1. If you see a person, face, animal, or pet, STOP and return exactly this: "
    "{\"error\": \"⚠️ HouseFix AI is speciaal ontworpen voor klussen, objecten en schade in of rondom het huis. Richt de camera alstublieft op het specifieke klusprobleem.\"}\n"
    "2. If the image clearly shows something completely unrelated to home repair (a car, food, landscape, phone screen, etc.), STOP and return exactly this: "
    "{\"error\": \"🔍 Dit object of deze situatie wordt niet herkend als een klusprobleem. Maak een nieuwe, duidelijke foto van de schade of het object.\"}\n\n"
    "UNCERTAIN - If you are not confident (less than 90% sure what the issue is OR less than "
    "80% sure what building element it is), or the image shows a plain wall/floor/ceiling "
    "without visible damage, then do NOT guess. Instead return: "
    "{\"needs_clarification\": true, \"questions\": ["
    "{\"id\": \"element\", \"question\": \"🏗️ Wat voor onderdeel van het huis is dit?\", \"options\": [\"Muur\", \"Plafond\", \"Vloer\", \"Dak\", \"Kozijn/raam\", \"Leiding/kraan\", \"Tegelwerk\", \"Tuin\", \"Anders\"]},"
    "{\"id\": \"size\", \"question\": \"📏 Hoe groot is het probleem ongeveer?\", \"options\": [\"Klein (pleisterformaat)\", \"Middel (handformaat)\", \"Groot (groter dan 50 cm)\"]},"
    "{\"id\": \"location\", \"question\": \"🏠 Is het binnen of buiten?\", \"options\": [\"Binnen\", \"Buiten\"]},"
    "{\"id\": \"water\", \"question\": \"💧 Komt er vocht/natte plekken bij kijken?\", \"options\": [\"Ja, het is nat\", \"Nee, het is droog\", \"Weet ik niet\"]}"
    "]}\n\n"
    "ONLY if there is CLEAR, VISIBLE damage AND you are at least 90% confident AND at least "
    "80% confident of the building element, analyze it and return valid JSON with these keys:\n"
    "building_element (the identified element: muur/plafond/vloer/dak/kozijn/leiding/tegelwerk/tuin/overig),\n"
    "issue_type (short, precise label in Dutch, 1-3 words like 'scheur in muur',\n"
    "'mos op hout', 'verweerd terras', or 'groene aanslag op voegen'),\n"
    "description (1-2 concise sentences in Dutch. Vertel de huiseigenaar wat het "
    "probleem is, wat de oorzaak is, en waarom het belangrijk is om er iets aan "
    "te doen. Niet alleen 'dit is een scheur' — maar 'dit is een scheur in je "
    "muur, die kan groeien als je er niets aan doet'. Leg ook uit waarom deze "
    "aanpak de beste keuze is voor deze specifieke situatie. Waarom bijvoorbeeld "
    "zelf doen de voorkeur heeft boven een vakman, of andersom. "
    "Waarom dit materiaal het beste past bij dit soort ondergrond of probleem. "
    "Dit geeft de huiseigenaar vertrouwen om een beslissing te nemen),\n"
    "steps (an array of 4-5 short, direct DIY repair steps in Dutch),\n"
    "materials (an array of specific materials/tools available at Gamma or Praxis),\n"
    "cost_diy (string like '€15 - €35' for materials only),\n"
    "cost_pro (string like '€100 - €250' for professional including travel costs),\n"
    "cost_range (string like '€50 - €250' overall range),\n"
    "confidence (high/medium/low).\n"
    "Always return ALL 9 fields. Wees precies met kosten. "
    "Denk aan de huiseigenaar — vertel hem wat hij moet weten, "
    "niet alleen wat je ziet. "
    "If there is ANY visible issue, report it."
)

INSPIRATION_PROMPT = (
    "You are a warm, betrokken en deskundige persoonlijke interieuradviseur. Een "
    "gebruiker heeft je een foto gestuurd met een specifiek doel. Jouw taak is om "
    "gepersonaliseerd advies te geven op basis van de foto EN het doel van de gebruiker.\n\n"
    "De gebruiker heeft eerst een oriëntatie-fase doorlopen waarin je de stijl hebt "
    "herkend. Nu heeft hij/zij een doel gekozen. Gebruik de oriëntatie-context en "
    "het doel om advies op maat te geven.\n\n"
    "STRUCTURED APPROACH:\n"
    "STEP 1 — Identify the style and explain why it fits. Kijk naar de foto en reageer "
    "natuurlijk. Begin niet met 'deze ruimte heeft...' maar reageer zoals je tegen "
    "een vriend zou zeggen: 'Wat een ontzettend fijne kamer!' of 'Oh, dit is echt "
    "een plaatje!'. Benoem daarna wat de stijl is en waarom het werkt — de kleuren, "
    "materialen, meubels en sfeer.\n"
    "STEP 2 — Help de gebruiker deze look te creëren. Geef suggesties voor meubels, "
    "kleuren, accessoires en winkels die bij deze stijl passen. Wat kan de gebruiker "
    "kopen, waar, en waarom past het?\n"
    "STEP 3 — Geef 1 kleine styling_tip: wat kan de gebruiker MORGEN al doen om deze "
    "look nog mooier te maken? Een kussen, plant, lamp of accessoire.\n\n"
    "ABSOLUTELY FORBIDDEN: You MUST NOT look for damage, cracks, leaks, rot, peeling paint, or repairs. "
    "This is an INSPIRATION mode. The user wants to know about style, not find problems.\n"
    "• Chairs, tables, sofas, beds, carpets, curtains, lamps are INTERIOR OBJECTS — not damage.\n"
    "• Clean concrete, brick, rough wood, worn surfaces are DESIGN CHOICES — not damage.\n"
    "• If you see a person, face, animal, or pet, STOP and return exactly this: "
    "{\"error\": \"⚠️ HouseFix AI Interieur kan geen gezichten of dieren analyseren. Richt op het interieur.\"}\n"
    "• If the image is completely unrelated (car, food, landscape, screen), STOP and return: "
    "{\"error\": \"🔍 Dit is niet herkend als interieur- of designfoto. Probeer een foto van een ruimte, meubel of materiaal.\"}\n\n"
    "═══ GOAL PERSONALIZATION ═══\n"
    "PAS JE ADVIES AAN OP BASIS VAN HET DOEL VAN DE GEBRUIKER.\n"
    "De gebruiker heeft een doel gekozen. Verander JE HELE OUTPUT op basis van dit doel — "
    "niet alleen de toon, maar ook de inhoud en nadruk van elk JSON-veld.\n\n"
    "Per doel pas je deze velden aan:\n\n"
    "DOEL 1 — 'Ik wil deze look namaken — geef me winkeladvies'\n"
    "  description: Praktisch 'hoe namaken'. Specifiek: waar koop je dit, waar let je op, "
    "wat kost het. Niet alleen beschrijven, maar een routekaart geven.\n"
    "  colors: EXACTE verfkleuren met merk én productnaam. Bijv. 'Flexa Zacht Zand 02.02' "
    "of 'Histor Natuurwit 1201'. Geef bij elke kleur een Gamma/Praxis link.\n"
    "  materials: Specifiek — welk hout, welke stof, welke afwerking. Waar te koop.\n"
    "  matching_stores: 3-4 specifieke winkels met productnaam, prijsindicatie, en "
    "waarom het past. Bijv. IKEA KALLAX kast ca. EUR 89 — past door strakke lijnen "
    "en past bij de Scandinavische uitstraling. Ook kleinere Nederlandse zaken als "
    "De Bommel, Woonexpress, of Leen Bakker.\n"
    "  styling_tip: Het eerste wat je moet kopen. Eén concreet startproduct.\n"
    "  gamma_tips: Verf, kwasten, roller — materialen om zelf te schilderen.\n\n"
    "DOEL 2 — 'Ik wil mijn interieur verbeteren — geef me haalbare tips'\n"
    "  description: Focus op evolutie, niet complete make-over. Wat kan de gebruiker "
    "VERANDEREN? Kleine aanpassingen die groot verschil maken. Denk aan de bestaande "
    "inrichting — bouw voort op wat er al is.\n"
    "  colors: Accentkleuren — wat kun je TOEVOEGEN aan een bestaand palette. "
    "Kleuren die makkelijk te combineren zijn. Kies voor Gamma/Praxis verf.\n"
    "  materials: Betaalbare alternatieven. Huurder-vriendelijke opties (geen boren, "
    "wel stickers, posters, losse meubels).\n"
    "  matching_stores: 2-3 winkels met focus op accessoires en kleine meubels. "
    "IKEA, HEMA, Woonmall. Concrete prijzen. Wat kost het?\n"
    "  styling_tip: 'Dit weekend te doen'. Een actie van maximaal een middag.\n"
    "  gamma_tips: Verf + kwasten + accessoires om te verven.\n\n"
    "DOEL 3 — 'Ik zoek inspiratie voor een nieuwe stijlrichting'\n"
    "  description: Stijleducatie — WAT voor stijl is dit, waar komt het vandaan, "
    "welke varianten zijn er? Niet alleen 'dit is Scandinavisch' maar 'dit is "
    "Scandinavisch met Japanse invloeden (Japandi), herkenbaar aan...' Geef de "
    "gebruiker taal en context om zijn eigen smaak te ontdekken.\n"
    "  colors: Breder kleurpalet met uitleg WAAROM deze kleuren bij deze stijl horen. "
    "Denk aan kleurenleer: complementair, monochroom, etc.\n"
    "  materials: Leg uit WAAROM deze materialen de stijl bepalen. Linnen = warmte, "
    "beton = industrieel, hout = natuurlijk.\n"
    "  matching_stores: Showrooms, woonboulevards, inspiratiewebsites. Ook online "
    "bronnen zoals Pinterest, VT Wonen, of Eigen Huis & Interieur.\n"
    "  similar_styles: Breid uit naar 2-3 verwante stijlen met uitleg. "
    "Bijv. 'Dit lijkt op Scandinavian, maar heeft ook elementen van Mid-Century Modern.'\n"
    "  styling_tip: Een richtinggevende tip — 'Ontdek deze stijl verder door te letten "
    "op...' Niet een product, maar een lens om door te kijken.\n"
    "  gamma_tips: Alleen als er verf of materialen worden genoemd.\n\n"
    "DOEL 4 — 'Ik ben gewoon benieuwd — vertel me wat dit is'\n"
    "  description: Beschrijvend en educatief. Wat maakt dit bijzonder? Waarom werkt "
    "het? Vertel alsof je een vriend(in) meeneemt door een museum. Waardering, "
    "geeft de gebruiker oog voor detail.\n"
    "  colors: Beschrijvend — benoem de kleuren en leg uit hoe ze samenwerken. "
    "Geen shopadvies, tenzij de gebruiker erom vraagt.\n"
    "  materials: Identificeer en verklaar. 'Dit is eiken fineer — zie je de "
    "nerf? Dat geeft warmte.'\n"
    "  matching_stores: 'Als je dit mooi vindt, kijk dan eens bij...' — "
    "inspirerend, niet dwingend. 1-2 suggesties, geen prijzen.\n"
    "  styling_tip: Een eye-opener — iets om op te letten. 'Kijk eens hoe het licht "
    "op dit materiaal valt — dat maakt de sfeer.'\n"
    "  gamma_tips: Leeg — niet nodig tenzij expliciet gevraagd.\n"
    "  confidence: Altijd 'high' als je zeker bent — twijfel niet bij dit doel.\n\n"
    "═══ EINDE PERSONALISATIE ═══\n\n"
    "Return valid JSON with these keys:\n"
    "style (short description of the interior style in Dutch),\n"
    "description (2-4 sentences in Dutch. Begin met een enthousiaste, natuurlijke "
    "reactie op de foto — 'Wat mooi!' of 'Dit is echt een prachtige ruimte!'. "
    "Vertel daarna waarom de stijl werkt: welke kleuren, materialen, meubels en "
    "licht zorgen voor de sfeer. PAS AAN OP BASIS VAN HET DOEL. "
    "Leg uit waarom de geadviseerde producten, kleuren en stijl juist bij deze "
    "specifieke ruimte passen — niet alleen in het algemeen. "
    "Het mag niet klinken als een rapport of beschrijving — het moet voelen "
    "alsof een interieuradviseur persoonlijk advies geeft),\n"
    "colors (an array of 4-6 specific colors in Dutch with paint brand suggestions, "
    "e.g. 'Flexa Natural Beige' or 'Histor Warm Zand'),\n"
    "materials (an array of visible materials in Dutch),\n"
    "matching_stores (an array of 2-3 specific product recommendations, EACH as a JSON object:\n"
    "  {\"store\": \"IKEA\", \"product\": \"KALLAX kast 147×77 cm\", \"price\": \"€89\", \"why\": \"Past door strakke lijnen bij de raamverdeling\"}\n"
    "  - store: winkelnaam (IKEA, HEMA, Leen Bakker, etc.)\n"
    "  - product: productnaam + maat/kleur specificatie\n"
    "  - price: exacte prijs in € (niet 'ca.' of range)\n"
    "  - why: waarom dit product past bij deze specifieke ruimte en stijl — niet algemeen, maar persoonlijk\n"
    "),\n"
    "options (an array of 2-3 personalized style variants, each as:\n"
    "  {\"name\": \"Scandinavisch licht\", \"description\": \"Waarom deze variant werkt\", \"colors\": [...], \"materials\": [...], \"stores\": [same structure as matching_stores]}\n"
    "  - name: korte variantnaam in Nederlands\n"
    "  - description: waarom dit een goed alternatief is\n"
    "  - colors: 3-4 kleuren specifiek voor deze variant\n"
    "  - materials: 2-4 materialen specifiek voor deze variant\n"
    "  - stores: 2-3 product recommendations — same object format as matching_stores\n"
    "  Maak de eerste optie altijd de aanbevolen keuze (optie A). De andere opties zijn alternatieven.\n"
    "),\n"
    "similar_styles (an array of 1-2 related style names with brief explanation),\n"
    "styling_tip (1 short, concrete tip in Dutch that the user can apply tomorrow — "
    "e.g. 'Voeg een rotan lamp toe voor een warme sfeer' or 'Een groot groen blad "
    "geeft direct die jungle vibe'),\n"
    "gamma_tips (an array of 1-2 specific products from Gamma/Praxis if paint or "
    "materials are mentioned, otherwise empty array),\n"
    "confidence (high/medium/low).\n"
    "Always return ALL 9 fields. Schrijf alsof je tegen een vriend praat — "
    "warm, persoonlijk en behulpzaam. Geen formele beschrijvingen, maar "
    "echt advies van iemand die verstand heeft van interieur. "
    "Never mention damage, repair, or problems."
)

ORIENTATION_PROMPT = (
    "You are a warm, betrokken interieuradviseur. Een gebruiker stuurt je een foto "
    "van zijn/haar interieur en wil een eerste indruk.\n\n"
    "Jouw taak is om een ORIËNTATIE te geven — dit is stap 1 van een gesprek. "
    "Je geeft NOG GEEN shopadvies, kleuradvies, stappenplan of stylingtips. "
    "Alleen een warme reactie en herkenning van de stijl.\n\n"
    "Reageer natuurlijk, alsof je tegen een vriend(in) praat die je zijn/haar "
    "nieuwe interieur laat zien. 'Wat een ontzettend mooie kamer!' of "
    "'Oh, dit is echt een plaatje! Wat een sfeer!'\n\n"
    "Benoem de stijl (Scandinavisch, Japandi, Modern, Industrieel, Bohemian, "
    "Klassiek, etc.) en vertel kort waarom het werkt — welke kleuren, materialen "
    "en elementen de sfeer bepalen.\n\n"
    "ABSOLUTELY FORBIDDEN: You MUST NOT look for damage, cracks, leaks, rot, peeling paint, or repairs. "
    "This is an INSPIRATION mode.\n"
    "• Chairs, tables, sofas, beds, carpets, curtains, lamps are INTERIOR OBJECTS — not damage.\n"
    "• Clean concrete, brick, rough wood, worn surfaces are DESIGN CHOICES — not damage.\n"
    "• NEVER mention products, stores, prices, or shopping advice.\n"
    "• NEVER give step-by-step plans or DIY instructions.\n"
    "• If you see a person, face, animal, or pet, return: "
    "{\"error\": \"⚠️ HouseFix AI kan geen gezichten of dieren analyseren. Richt op het interieur.\"}\n"
    "• If the image is completely unrelated, return: "
    "{\"error\": \"🔍 Dit is niet herkend als interieurfoto. Probeer een foto van een ruimte of interieur.\"}\n\n"
    "Altijd je beste interpretatie geven — nooit om verduidelijking vragen. "
    "Zelfs als je niet 100% zeker bent, geef dan je beste inschatting.\n\n"
    "Return valid JSON with these keys:\n"
    "style (korte stijlbenaming in het Nederlands, 1-3 woorden, e.g. 'Scandinavisch' or 'Modern industrieel'),\n"
    "reaction (1 warme zin als eerste reactie, natuurlijk en enthousiast, "
    "alsof je tegen een vriend praat, e.g. 'Wat een prachtige, lichte kamer!'),\n"
    "style_explanation (1-2 zinnen over waarom deze stijl werkt — welke kleuren, "
    "materialen en elementen de sfeer bepalen. Niet alleen beschrijven, maar uitleggen "
    "waarom het bij elkaar past),\n"
    "vibe (1 woord dat de sfeer beschrijft, e.g. 'rustig', 'speels', 'luxe', 'warm', 'fris'),\n"
    "confidence (high/medium/low — wees eerlijk maar geef altijd je beste gok).\n"
    "Always return ALL 5 fields."
)

# ── Session Cache for multi-step conversation ──
SESSION_CACHE = {}
SESSION_TTL = 3600  # 1 hour

def create_session(image_b64, orient_result):
    session_id = str(uuid.uuid4())
    SESSION_CACHE[session_id] = {
        'image': image_b64,
        'orient': orient_result,
        'created_at': time.time()
    }
    return session_id

def get_session(session_id):
    session = SESSION_CACHE.get(session_id)
    if session and time.time() - session['created_at'] < SESSION_TTL:
        return session
    return None

def cleanup_sessions():
    now = time.time()
    expired = [sid for sid, s in SESSION_CACHE.items()
               if now - s['created_at'] > SESSION_TTL]
    for sid in expired:
        del SESSION_CACHE[sid]

# ── Fallback orientation data ──
FALLBACK_ORIENT = [
    {"style": "Scandinavisch", "reaction": "Wat een prachtige, lichte ruimte!", "style_explanation": "Deze stijl draait om eenvoud, natuurlijke materialen en licht. Wit houtwerk, lichte meubels en groene planten zorgen voor een rustige, frisse uitstraling.", "vibe": "rustig", "confidence": "high"},
    {"style": "Modern industrieel", "reaction": "Wow, wat een gave industriële uitstraling!", "style_explanation": "Ruwe materialen zoals beton en staal, gecombineerd met warm hout en leer. Open ruimtes met hoge plafonds en grote ramen kenmerken deze stijl.", "vibe": "stoer", "confidence": "high"},
    {"style": "Japandi", "reaction": "Wat een serene, minimalistische schoonheid!", "style_explanation": "De perfecte balans tussen Japanse eenvoud en Scandinavische gezelligheid. Natuurlijke materialen, neutrale kleuren en strakke lijnen creëren rust.", "vibe": "harmonisch", "confidence": "medium"},
    {"style": "Bohemian", "reaction": "Wat een heerlijk eclectische mix!", "style_explanation": "Kleurrijke texturen, wereldse accessoires en een ontspannen sfeer. Veel planten, kussens en unieke vondsten maken deze stijl persoonlijk en warm.", "vibe": "vrij", "confidence": "medium"},
]

# ── Fallback inspiration advice data (Fase 3: structured stores + options) ──
FALLBACK_INSPIRATION = [
    {
        "style": "Scandinavisch minimalisme",
        "description": "Wat een rustgevende, lichte uitstraling! Deze ruimte ademt Scandinavische eenvoud: wit als basis, natuurlijke materialen en strakke lijnen. De kunst is dat het niet kaal aanvoelt — elk object heeft een doel en draagt bij aan de balans.",
        "options": [
            {
                "name": "Scandinavisch licht",
                "description": "Blijf bij de lichte, luchtige basis met warme houtaccenten.",
                "colors": ["warm wit", "eiken", "saliegroen", "lichtgrijs"],
                "materials": ["eiken", "linnen", "wol", "keramiek"],
                "stores": [
                    {"store": "IKEA", "product": "KALLAX kast 147×77 cm", "price": "€89", "why": "Rasterstructuur herhaalt de strakke architectuurlijnen zonder te overheersen."},
                    {"store": "Leen Bakker", "product": "Linnen gordijn naturel 140×250 cm", "price": "€59,95", "why": "Linnen dempt licht op een zachte manier — precies wat deze ruimte nodig heeft."},
                    {"store": "HEMA", "product": "Keramieken vaas mat wit 30 cm", "price": "€14,95", "why": "Eenvoudig en tijdloos — de perfecte accessoire voor deze strakke stijl."}
                ]
            },
            {
                "name": "Warm Scandinavisch",
                "description": "Voeg diepte toe met warme accentkleuren zonder de rust te breken.",
                "colors": ["terracotta", "crème", "koper", "mosterd"],
                "materials": ["velours", "rotan", "koper", "eiken"],
                "stores": [
                    {"store": "IKEA", "product": "STRANDMAL hanglamp rotan", "price": "€39,95", "why": "Rotan geeft warmte en textuur — breekt het strakke zonder rommelig te worden."},
                    {"store": "HEMA", "product": "Koperen kaarshouder set 3-stuks", "price": "€12,95", "why": "Koper accenten brengen licht en warmte in de ruimte, vooral in de avond."},
                    {"store": "De Bommel", "product": "Velours kussen mosterd 45×45 cm", "price": "€24,99", "why": "Mosterd accent verbindt het warme hout met de lichte muur — een subtiele blikvanger."}
                ]
            },
            {
                "name": "Natuur-inspiratie",
                "description": "Haal de buitenlucht naar binnen met organische vormen en aardse tinten.",
                "colors": ["olijfgroen", "zand", "bruin", "crème"],
                "materials": ["linnen", "keramiek", "rotan", "steen"],
                "stores": [
                    {"store": "Intratuin", "product": "Olijfboom 120 cm pot", "price": "€59,95", "why": "Een olijfboom brengt hoogte, textuur en een mediterraan gevoel — dé blikvanger."},
                    {"store": "Leen Bakker", "product": "Rotan bijzettafel naturel", "price": "€44,95", "why": "Organische vorm die de strakke lijnen verzacht zonder te contrasteren."}
                ]
            }
        ],
        "colors": ["warm wit", "eiken", "saliegroen", "lichtgrijs"],
        "materials": ["eiken", "linnen", "wol", "keramiek"],
        "matching_stores": [
            {"store": "IKEA", "product": "KALLAX kast 147×77 cm", "price": "€89", "why": "Past door strakke lijnen bij de ritmiek van de ruimte."},
            {"store": "Leen Bakker", "product": "Linnen gordijn naturel", "price": "€59,95", "why": "Zachte lichtinval zonder de ruimte donker te maken."}
        ],
        "similar_styles": ["Japandi", "Modern klassiek"],
        "styling_tip": "Begin met de rotan hanglamp — die verandert de sfeer in één middag zonder te verven of boren.",
        "primary_action": "Hang de STRANDMAL lamp boven de eettafel voor warmte en textuur.",
        "confidence": "high"
    },
    {
        "style": "Modern industrieel",
        "description": "Wat een stoere, rauwe uitstraling! Beton, staal en hout komen hier perfect samen. De open ruimte en hoge plafonds vragen om sterke, architecturale keuzes — geen rommel, geen overbodige decoratie.",
        "options": [
            {
                "name": "Licht industrieel",
                "description": "Verzacht het beton met warm hout en leer voor een uitnodigende sfeer.",
                "colors": ["betongrijs", "zwart", "eiken", "olijfgroen"],
                "materials": ["eiken", "leer", "beton", "staal"],
                "stores": [
                    {"store": "IKEA", "product": "KIVIK bank 3-zits zwart", "price": "€899", "why": "Strak, zwart frame past bij het industriële palet — leer gaat jaren mee."},
                    {"store": "Karwei", "product": "Planken eiken 200×25 cm (onbehandeld)", "price": "€24,95", "why": "Zwevende planken verzachten de betonnen muur zonder deze te bedekken."}
                ]
            },
            {
                "name": "Ruw industrieel",
                "description": "Omarm het rauwe met donkere accenten en metalen details.",
                "colors": ["antraciet", "zwart", "roestbruin", "koper"],
                "materials": ["staal", "beton", "glas", "leer"],
                "stores": [
                    {"store": "Karwei", "product": "Metallic wandkast antraciet 80×30 cm", "price": "€79,95", "why": "Metalen kast accentueert de industriële look — functioneel en stoer."},
                    {"store": "HEMA", "product": "Glazen decoratiefles zwart 3-stuks", "price": "€17,95", "why": "Donker glas past bij de rauwe esthetiek zonder extra kleur toe te voegen."}
                ]
            }
        ],
        "colors": ["betongrijs", "zwart", "eiken", "olijfgroen"],
        "materials": ["eiken", "leer", "beton", "staal"],
        "matching_stores": [
            {"store": "IKEA", "product": "KIVIK bank 3-zits zwart", "price": "€899", "why": "Strak, zwart frame voor een industriële basis."},
            {"store": "Karwei", "product": "Zwevende planken eiken 200×25 cm", "price": "€24,95", "why": "Verzacht beton zonder het te bedekken."}
        ],
        "similar_styles": ["Loft", "Brutalistisch"],
        "styling_tip": "Vervang de gordijnen door jaloezieën — dat versterkt de industriële lijnvoering.",
        "primary_action": "Installeer zwevende eiken planken langs de betonmuur.",
        "confidence": "high"
    },
    {
        "style": "Japandi",
        "description": "Wat een serene balans tussen eenvoud en warmte! Japandi is de perfecte symbiose van Japanse minimalisme en Scandinavische hygge. Elk detail is bewust gekozen — niets staat er per ongeluk.",
        "options": [
            {
                "name": "Minimalistisch Japandi",
                "description": "Ga voor volledige rust met een monochroom palet en natuurlijke texturen.",
                "colors": ["wit", "beige", "lichtgrijs", "zwart"],
                "materials": ["eiken", "linnen", "steen", "keramiek"],
                "stores": [
                    {"store": "IKEA", "product": "HEMNES bijzettafel wit 55×55 cm", "price": "€59,95", "why": "Massief hout met strakke lijnen — Japandi in meubelvorm."},
                    {"store": "HEMA", "product": "Linnen placemat naturel set 4", "price": "€14,95", "why": "Linnen textuur voegt warmte toe zonder visuele ruis."},
                    {"store": "Leen Bakker", "product": "Stenen vaas mat zwart 20 cm", "price": "€19,95", "why": "Zware, organische vorm die de rust verankert."}
                ]
            },
            {
                "name": "Warm Japandi",
                "description": "Voeg diepe houttinten en groene accenten toe voor een aardse variant.",
                "colors": ["donker eiken", "olijfgroen", "crème", "zwart"],
                "materials": ["donker eiken", "linnen", "keramiek", "bamboe"],
                "stores": [
                    {"store": "IKEA", "product": "BESTÅ kast donker eiken 120×40 cm", "price": "€249", "why": "Donker hout geeft diepte aan het lichte palet — functioneel en sculpturaal."},
                    {"store": "Intratuin", "product": "Bamboe plantenstandaard 80 cm", "price": "€34,95", "why": "Bamboe past perfect bij de natuurlijke, Aziatische invloeden van Japandi."}
                ]
            }
        ],
        "colors": ["wit", "beige", "lichtgrijs", "zwart"],
        "materials": ["eiken", "linnen", "steen", "keramiek"],
        "matching_stores": [
            {"store": "IKEA", "product": "HEMNES bijzettafel wit 55×55 cm", "price": "€59,95", "why": "Massief hout, strakke lijnen — de essentie van Japandi."},
            {"store": "HEMA", "product": "Linnen placemat naturel set 4", "price": "€14,95", "why": "Textuur zonder visuele ruis."}
        ],
        "similar_styles": ["Zen", "Wabi-sabi"],
        "styling_tip": "Rol een tatami-mat uit onder de zithoek — dat geeft direct een Japanse basis.",
        "primary_action": "Vervang je bijzettafel door een HEMNES in massief hout.",
        "confidence": "high"
    },
    {
        "style": "Bohemian",
        "description": "Wat een feest van kleur en textuur! Deze ruimte vertelt een verhaal met wereldse accessoires, warme tinten en laagjes textiel. Het voelt ontspannen en uitnodigend — alsof je in een verre reis bent beland.",
        "options": [
            {
                "name": "Boho natuurlijk",
                "description": "Aardse tinten en natuurlijke materialen voor een geborgen sfeer.",
                "colors": ["terracotta", "mosterd", "olijfgroen", "crème"],
                "materials": ["katoen", "rotan", "keramiek", "wol"],
                "stores": [
                    {"store": "HEMA", "product": "Wollen katoenkleed gevlochten 140×200 cm", "price": "€39,95", "why": "Gevlochten textiel voegt laagjes toe — de basis van elke boho-inrichting."},
                    {"store": "Intratuin", "product": "Hangplant in rotan mand 25 cm", "price": "€24,95", "why": "Groen in rotan — dé boho-combinatie die hoogte en leven brengt."}
                ]
            },
            {
                "name": "Boho kleurrijk",
                "description": "Durf met kleur! Oranje, rood en blauw in een speelse mix.",
                "colors": ["oranje", "koraal", "indigo", "goud"],
                "materials": ["zijde", "fluweel", "katoen", "glas"],
                "stores": [
                    {"store": "IKEA", "product": "GURLI kussen 50×50 cm oranje", "price": "€12,95", "why": "Betaalbaar statement-kussen dat de ruimte een kleurboost geeft."},
                    {"store": "De Bommel", "product": "Fluwelen kussen koraal 45×45 cm", "price": "€29,99", "why": "Fluweel voegt luxe textuur toe aan de relaxte boho-sfeer."}
                ]
            }
        ],
        "colors": ["terracotta", "mosterd", "olijfgroen", "crème"],
        "materials": ["katoen", "rotan", "keramiek", "wol"],
        "matching_stores": [
            {"store": "HEMA", "product": "Gevlochten katoenkleed 140×200 cm", "price": "€39,95", "why": "Laagjes textiel voor de boho-basis."},
            {"store": "Intratuin", "product": "Hangplant rotan 25 cm", "price": "€24,95", "why": "Groen in rotan geeft hoogte en leven."}
        ],
        "similar_styles": ["Eclectisch", "Mid-Century Modern"],
        "styling_tip": "Hang een macramé plantenhanger voor het raam — dat geeft hoogte en textuur in één.",
        "primary_action": "Leg het wollen katoenkleed onder de zithoek voor laagjes warmte.",
        "confidence": "medium"
    }
]


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
    """Multi-step analysis endpoint.
    
    Accepts:
      - image (base64)
      - mode: "damage" | "inspiration"
      - step: "orient" (inspiration step 1) | "advise" (inspiration step 2)
      - session_id (for step 2)
      - goal (for step 2: the user's chosen archetype)
    
    Flow for inspiration mode:
      1. POST with step="orient" → returns orientation + session_id
      2. POST with step="advise" + session_id + goal → returns personalized advice
    
    Damage mode: unchanged (single step).
    """
    import re as regex_module

    try:
        data = request.get_json()
    except Exception:
        return jsonify({"error": "Invalid JSON body"}), 400

    if not data or "image" not in data:
        return jsonify({"error": "No image provided"}), 400

    image_base64 = data["image"]
    mode = data.get("mode", "damage")
    step = data.get("step", None)

    if not isinstance(image_base64, str) or len(image_base64) < 100:
        return jsonify({"error": "Invalid image data"}), 400

    # If no API key, return fallback (damage mode) or orientation fallback
    if not OPENAI_API_KEY:
        if mode == "inspiration" and step == "orient":
            fallback = random.choice(FALLBACK_ORIENT)
            session_id = create_session(image_base64, fallback)
            return jsonify({"orient": fallback, "session_id": session_id})
        elif mode == "inspiration" and step == "advise":
                        return jsonify(random.choice(FALLBACK_INSPIRATION))
        return jsonify(random.choice(FALLBACK_ISSUES))

    # ── INSPIRATION MODE: STEP 1 — Orientation ──
    if mode == "inspiration" and step == "orient":
        try:
            client = OpenAI(api_key=OPENAI_API_KEY)
            response = client.chat.completions.create(
                model="gpt-4o",
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": ORIENTATION_PROMPT},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Geef een eerste indruk van deze ruimte."},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}},
                        ],
                    },
                ],
                max_tokens=400,
                temperature=0.3,
            )
            message = response.choices[0].message.content
            json_match = regex_module.search(r'\{.*\}', message, regex_module.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                if isinstance(parsed, dict) and "error" in parsed:
                    return jsonify({"warning": parsed["error"]})
                # Store in session cache
                session_id = create_session(image_base64, parsed)
                return jsonify({"orient": parsed, "session_id": session_id})
        except Exception as e:
            app.logger.error(f"Orientation error: {e}")
            fallback = random.choice(FALLBACK_ORIENT)
            session_id = create_session(image_base64, fallback)
            return jsonify({"orient": fallback, "session_id": session_id})
        return jsonify({"orient": random.choice(FALLBACK_ORIENT)})

    # ── INSPIRATION MODE: STEP 2 — Personalized Advice ──
    if mode == "inspiration" and step == "advise":
        session_id = data.get("session_id", "")
        goal = data.get("goal", "")
        session = get_session(session_id)

        # Build context from session
        context_parts = []
        if session:
            orient = session.get('orient', {})
            context_parts.append(f"Eerste indruk van deze ruimte: {orient.get('style', 'onbekend')} — {orient.get('style_explanation', '')}")
            context_parts.append(f"Sfeer: {orient.get('vibe', '')}")
            # Use stored image
            image_base64 = session.get('image', image_base64)
        else:
            context_parts.append("Geen eerdere sessie gevonden — geef advies op basis van de foto alleen.")

        if goal:
            context_parts.append(f"DOEL VAN DE GEBRUIKER: {goal}")

        user_context = "\n".join(context_parts)

        try:
            client = OpenAI(api_key=OPENAI_API_KEY)
            full_prompt = INSPIRATION_PROMPT + (
                f"\n\nCONTEXT VAN EERDERE STAP:\n{user_context}\n\n"
                "Gebruik deze context om je advies te personaliseren. "
                "Het doel van de gebruiker is hierboven vermeld — pas je hele advies daarop aan."
            )
            response = client.chat.completions.create(
                model="gpt-4o",
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": full_prompt},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Geef gepersonaliseerd advies op basis van de context en het doel."},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}},
                        ],
                    },
                ],
                max_tokens=700,
                temperature=0.2,
            )
            message = response.choices[0].message.content
            json_match = regex_module.search(r'\{.*\}', message, regex_module.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                if isinstance(parsed, dict) and "error" in parsed:
                    return jsonify({"warning": parsed["error"]})
                if isinstance(parsed, dict) and ("style" in parsed or "issue_type" in parsed):
                    return jsonify(parsed)
        except Exception as e:
            app.logger.error(f"Advise error: {e}")
            return jsonify({"error": str(e)}), 500

        return jsonify({"style": "Stijl niet herkend", "description": "Er is iets misgegaan bij het genereren van het advies.", "confidence": "low"})

    # ── DAMAGE MODE OR LEGACY INSPIRATION (single step) ──
    answers = data.get("answers", None)
    base_prompt = INSPIRATION_PROMPT if mode == "inspiration" else SYSTEM_PROMPT

    if answers and len(answers) > 0:
        context_lines = [f"{a['question']} → {a['answer']}" for a in answers]
        user_context = "\n".join(context_lines)
        full_prompt = base_prompt + (
            f"\n\nThe user provided these details:\n{user_context}\n"
            "Now give your best, most accurate analysis based on the photo AND these details."
        )
        user_text = "Analyze with the context provided above."
    else:
        full_prompt = base_prompt
        user_text = "Analyze this image and return the JSON as instructed."

    try:
        client = OpenAI(api_key=OPENAI_API_KEY)

        response = client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": full_prompt},
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

        # Extract JSON from response
        json_match = regex_module.search(r'\{.*\}', message, regex_module.DOTALL)
        if json_match:
            parsed = json.loads(json_match.group())
            if isinstance(parsed, dict) and "error" in parsed:
                return jsonify({"warning": parsed["error"]})
            if isinstance(parsed, dict) and parsed.get("no_damage"):
                return jsonify({"no_damage": True, "message": parsed.get("message", "✅ Geen schade geconstateerd.")})
            if isinstance(parsed, dict) and parsed.get("needs_clarification"):
                return jsonify({"needs_clarification": True, "questions": parsed.get("questions", [])})
            # Normal analysis result (damage: issue_type keys, inspiration: style key)
            if isinstance(parsed, dict) and ("issue_type" in parsed or "style" in parsed):
                return jsonify(parsed)

        return jsonify(random.choice(FALLBACK_ISSUES))

    except Exception as e:
        app.logger.error(f"Analyze error: {e}")
        return jsonify({"error": str(e), "fallback": random.choice(FALLBACK_ISSUES)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
