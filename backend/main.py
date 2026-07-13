from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import json
import random
import uuid
import time
import hashlib
from openai import OpenAI
import sqlite3
import re
import datetime

app = Flask(__name__)

@app.errorhandler(404)
@app.errorhandler(405)
@app.errorhandler(500)
def json_error_handler(e):
    """Return JSON for all errors, never HTML."""
    return jsonify({"status": "error", "message": str(e), "code": e.code if hasattr(e, 'code') else 500}), e.code if hasattr(e, 'code') else 500

@ app.errorhandler(Exception)
def json_unhandled_handler(e):
    """Catch-all: any unhandled exception returns JSON."""
    app.logger.error(f"Unhandled error: {e}")
    return jsonify({"status": "error", "message": "Internal server error"}), 500


# ---------------------------------------------------------------------------
# Product Catalog (standalone SQLite database)
# ---------------------------------------------------------------------------
CATALOG_DB = os.path.join(os.path.dirname(__file__), 'product_catalog.db')

def _parse_price_cents(price_str):
    if not price_str:
        return 0
    s = price_str.replace(chr(8364), '').replace(' ', '').replace('+', '').strip()
    if '-' in s:
        s = s.split('-')[0].strip()
    s = s.replace('.', '').replace(',', '.')
    try:
        return int(float(s) * 100)
    except:
        return 0

def _seed_catalog(cur, conn):
    n = 0
    for scenario in FALLBACK_PURCHASE:
        for seg_name, prods in scenario.get('segments', {}).items():
            for idx, p in enumerate(prods):
                name = p['name']
                store = p['store']
                price_cents = _parse_price_cents(p['price'])
                cat = p.get('category', 'accessoire')
                visual = p.get('visual', {})
                pal = json.dumps(visual.get('color_palette', []))
                mood = visual.get('mood', 'warm')
                style_tag = visual.get('style_tag', 'modern')
                featured = 1 if p.get('featured') else 0
                pid = 'prod_' + re.sub(r'[^a-z0-9]', '_', store.lower().strip()) + '_' + str(idx)
                cur.execute(
                    'INSERT OR IGNORE INTO products '
                    '(id, name, store, category, price_cents, currency, price_segment, '
                    'color_palette, mood, style_tag, featured, available, image_url, last_updated) '
                    'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)',
                    (pid, name, store, cat, price_cents, 'EUR', seg_name,
                     pal, mood, style_tag, featured, '',
                     datetime.datetime.now().isoformat()))
                n += 1
    conn.commit()
    return n

def init_catalog():
    conn = sqlite3.connect(CATALOG_DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(
        'CREATE TABLE IF NOT EXISTS products ('
        'id TEXT PRIMARY KEY, name TEXT NOT NULL, store TEXT NOT NULL, '
        'category TEXT, subcategory TEXT, style_tags TEXT, '
        'price_cents INTEGER, currency TEXT DEFAULT \'EUR\', '
        'price_segment TEXT, image_url TEXT, product_url TEXT, '
        'affiliate_url TEXT, affiliate_network TEXT, commission_pct REAL, '
        'color_palette TEXT, mood TEXT, style_tag TEXT, '
        'featured INTEGER DEFAULT 0, available INTEGER DEFAULT 1, '
        'last_updated TEXT)')
    cur.execute('SELECT COUNT(*) FROM products')
    if cur.fetchone()[0] == 0:
        count = _seed_catalog(cur, conn)
        print(f"Catalog: {count} products seeded")
    conn.close()

def get_catalog():
    """Thread-safe: fresh connection per call (check_same_thread=False)"""
    conn = sqlite3.connect(CATALOG_DB, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def search_catalog(q=None, store=None, segment=None, category=None, limit=5):
    conn = get_catalog()
    cur = conn.cursor()
    sql = 'SELECT * FROM products WHERE available = 1'
    params = []
    if q:
        sql += ' AND name LIKE ?'
        params.append('%' + q + '%')
    if store:
        sql += ' AND store = ?'
        params.append(store)
    if segment:
        sql += ' AND price_segment = ?'
        params.append(segment)
    if category:
        sql += ' AND category = ?'
        params.append(category)
    sql += ' ORDER BY featured DESC, name ASC LIMIT ?'
    params.append(min(limit, 100))
    cur.execute(sql, params)
    results = []
    for row in cur.fetchall():
        d = dict(row)
        pc = d.pop('price_cents', 0) or 0
        euros = pc // 100
        cents = pc % 100
        if cents:
            d['price'] = chr(8364) + str(euros) + ',' + str(cents).zfill(2)
        else:
            d['price'] = chr(8364) + str(euros)
        for fld in ('color_palette', 'style_tags'):
            val = d.get(fld)
            if val:
                try:
                    d[fld] = json.loads(val)
                except:
                    if fld == 'color_palette':
                        d[fld] = []
        results.append(d)
    return results

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
    "═══ SCENE TYPE ADAPTATIE ═══\n"
    "De gebruiker heeft in de oriëntatie-fase een 'scene_type' meegekregen. "
    "Pas je advies aan op basis van SCENE_TYPE:\n\n"
    "SCENE_TYPE = complete_room:\n"
    "  - Normale interieuranalyse: beschrijf de stijl, kleuren, materialen van de ruimte.\n"
    "  - Geef shopadvies voor meubels, accessoires en decoratie die de ruimte versterken.\n"
    "  - 3-4 producten uit verschillende segmenten (budget, midden, premium).\n"
    "  - De description beschrijft de RUIMTE, niet een enkel object.\n\n"
    "SCENE_TYPE = object_closeup:\n"
    "  - Dit is een close-up van een specifiek object (vaas, lamp, stoel, tafel) met beperkte context.\n"
    "  - Beschrijf HET OBJECT, niet een complete ruimte. Wat is het? Welk materiaal? Welke stijl?\n"
    "  - Geef GEEN shopadvies voor een volledige ruimte-inrichting. Richt je op:\n"
    "    * Hoe dit object past in 2-3 verschillende interieurstijlen (bv. Scandinavisch, Bohemian)\n"
    "    * Vergelijkbare objecten in andere stijlen (bv. 'deze vaas in keramiek past bij Scandinavisch, een rotan variant past bij Bohemian')\n"
    "    * Hoe je dit object kunt combineren (bv. 'zet er een tak eucalyptus in voor een natuurlijk accent')\n"
    "  - matching_stores en stores in options: max 1-2 producten, gericht op accessoires die bij DIT OBJECT passen.\n"
    "  - colors: de kleuren van het object + 1-2 accentkleuren die erbij passen (niet een volledig ruimtepalet).\n"
    "  - materials: de materialen van het object + 1-2 materialen die er goed mee combineren.\n"
    "  - De description begint met het object ('Wat een prachtige minimalistische vaas!') niet met een ruimte.\n\n"
    "SCENE_TYPE = texture_detail:\n"
    "  - Dit is een detailopname van een materiaal of textuur.\n"
    "  - Beschrijf HET MATERIAAL: wat is het, welke eigenschappen heeft het, welke sfeer geeft het?\n"
    "  - Geef GEEN shopadvies. In plaats daarvan: bij welke interieurstijlen past dit materiaal?\n"
    "  - matching_stores en stores in options: leeg laten ([]).\n"
    "  - colors: max 2-3 kleuren die bij dit materiaal passen.\n"
    "  - materials: het materiaal zelf + 1-2 complementaire materialen.\n\n"
    "SCENE_TYPE = unclear:\n"
    "  - Je kunt niet goed bepalen wat er op de foto staat.\n"
    "  - Geef een eerlijke, zachte reactie: je herkent niet genoeg details voor een advies.\n"
    "  - matching_stores en stores in options: leeg laten ([]).\n"
    "  - Beschrijf wat je WEL ziet (kleuren, vormen) en nodig uit om een betere foto te maken.\n"
    "  - styling_tip: 'Maak een foto van de hele ruimte of van het object dat je wilt bespreken.'\n\n"
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

# ── IDENTIFY PROMPT ──
IDENTIFY_PROMPT = (
    "You are a warme, deskundige interieur- en designexpert. Je hebt oog voor detail, "
    "kent designgeschiedenis en kunt objecten duiden alsof je in een museum staat.\n\n"
    "Een gebruiker heeft een foto gestuurd van een object en wil weten WAT het is. "
    "Niet wat hij ermee moet doen, niet hoe hij het moet stylen — maar: wat is dit, "
    "waar komt het vandaan, welk ontwerp, welk materiaal, waarom is het bijzonder?\n\n"
    "Jouw taak is om een diepgaande, persoonlijke IDENTIFICATIE te geven. "
    "Geen droge opsomming, maar een verhaal dat de gebruiker het gevoel geeft "
    "dat hij naast een kenner staat die met passie over design vertelt.\n\n"
    "STAP 1 — IDENTIFICEER HET OBJECT: Wat is het precies? Benoem het type object "
    "(vaas, lamp, stoel, tafel, sculptuur, etc.), het dominante materiaal, de "
    "vormgeving en de afwerking. Wees specifiek: 'een handgedraaide keramieken vaas "
    "met mat saliegroen glazuur' in plaats van 'een groene vaas'.\n\n"
    "STAP 2 — BEPAAL DE STIJL EN DESIGNPERIODE: Welke ontwerpstroming hoort hierbij? "
    "(Japandi, Scandinavian modern, Art Deco, Bauhaus, Memphis, Mid-Century Modern, "
    "Wabi-sabi, etc.) Dateer het ontwerp indien mogelijk in een periode of decennium. "
    "Leg uit WAAROM je deze stijl herkent: welke kenmerken verwijzen ernaar?\n\n"
    "STAP 3 — GEEF CONTEXT: Hoe wordt dit object normaal toegepast in een interieur? "
    "In welke setting komt het het beste tot zijn recht? Wat zegt dit object over de "
    "smaak van de eigenaar? Dit is geen shopadvies, maar een cultuurhistorische of "
    "esthetische duiding.\n\n"
    "STAP 4 — SLUIT AF MET EEN PERSOONLIJKE OPMERKING: Wat maakt dit object de moeite "
    "waard? Waarom is het bijzonder dat de gebruiker dit object heeft? Dit hoeft niet "
    "groots te zijn — een kleine, oprechte observatie is krachtiger dan een opgeklopt verhaal.\n\n"
    "ABSOLUTELY FORBIDDEN:\n"
    "• Geef GEEN shopadvies, prijzen, winkels of koopinformatie.\n"
    "• Geef GEEN stappenplannen of DIY-instructies.\n"
    "• Geef GEEN stylingtips voor de ruimte (dat is een andere intentie).\n"
    "• Zoek NIET naar schade, reparaties of gebreken — dit is een designanalyse.\n"
    "• Als je een persoon, gezicht of dier ziet: stop en retourneer "
    "{\"error\": \"⚠️ HouseFix AI kan geen gezichten of dieren analyseren.\"}\n"
    "• Als de foto volledig ongerelateerd is (auto, eten, landschap): stop en retourneer "
    "{\"error\": \"🔍 Dit is niet herkend als design- of interieurobject.\"}\n\n"
    "Return valid JSON with these keys:\n"
    "intent (altijd 'identify'),\n"
    "object_type (korte benaming van het object in Nederlands, e.g. 'Keramieken vaas', 'Designstoel', 'Tafellamp'),\n"
    "identification (een object met de volgende velden:\n"
    "  - type: uitgebreide beschrijving van het object (1 zin, e.g. 'Handgedraaide keramieken vaas met mat saliegroen glazuur')\n"
    "  - materials: lijst van materialen (e.g. ['keramiek', 'mat glazuur'])\n"
    "  - style: stijlbenaming (e.g. 'Japandi / Wabi-sabi')\n"
    "  - design_period: geschatte periode of ontwerpstroming (e.g. '1960-1980, studio pottery', 'Mid-Century Modern, 1950s')\n"
    "  - designer_hint: eventuele verwijzing naar een ontwerper of merk, alleen als aannemelijk (e.g. 'Doet denken aan Lucie Rie', 'Vermoedelijk ontworpen door Arne Jacobsen'). Wees voorzichtig — niet verzinnen.\n"
    "  - key_features: lijst van 2-4 opvallende ontwerpkenmerken (e.g. ['organische vorm', 'subtiele glazuurvariaties', 'ongelakte bodem'])\n"
    "  - why_special: 1 zin waarom dit object bijzonder is — niet algemeen, maar specifiek voor DIT exemplaar (e.g. 'De variatie in glazuurdikte maakt elke vaas uniek — dit is het kenmerk van ambachtelijk werk.')\n"
    "),\n"
    "style_context (1-2 zinnen over hoe dit object in een interieur past, welke sfeer het geeft, en bij welke interieurstijlen het aansluit. Dit is GEEN shopadvies, maar context),\n"
    "description (1 warme, natuurlijke alinea die het object beschrijft alsof je het aan een vriend laat zien in een museum. Begin met het object, niet met een ruimte. Vertel een verhaal — wat zie je, wat voel je, waarom is dit object de moeite waard om naar te kijken?),\n"
    "styling_tip (1 korte, concrete tip die niets met kopen te maken heeft. Hoe kun je dit object het beste laten zien? Bijv. 'Zet er een tak bloeiende kweepeer in voor een Wabi-sabi compositie.' of 'Plaats het op een sokkel van 40 cm hoog — dan komt de organische vorm beter tot zijn recht.'),\n"
    "confidence (high/medium/low — wees eerlijk. Als je twijfelt over de herkomst of het ontwerp, zeg dat dan. 'medium' met uitleg is beter dan 'high' zonder onderbouwing)."
)

# —— COLOR PALETTE PROMPT ——
COLOR_PALETTE_PROMPT = (
    "Je bent een ervaren interieurstylist met oog voor kleur en materiaal. "
    "Een gebruiker heeft een foto gestuurd en wil weten welk KLEURENPALET "
    "en welke VERF-/MATERIAALADVIEZEN bij deze ruimte of dit object passen.\n\n"
    "Jouw taak: analyseer de dominante kleuren in de foto en geef een compleet "
    "kleuradvies met verfkleuren en materialen.\n\n"
    "STAP 1 \u2014 BEPAAL HET KLEURENPALET: Welke 4-8 kleuren domineren de foto? "
    "Noem ze in het Nederlands \u2014 dit zijn de kleuren die een verfproducent "
    "zou beschrijven. Wees specifiek: 'saliegroen' in plaats van 'groen', "
    "'mosterdgeel' in plaats van 'geel'.\n\n"
    "STAP 2 \u2014 BEPAAL DE STIJL EN SFEER: Welke interieurstijl past bij dit palet? "
    "(Japandi, Scandinavian, Rustiek, Industrieel, Boho, Modern, etc.) "
    "Wat is de sfeer? (rustiek warm, minimalistisch koel, speels eclectisch)\n\n"
    "STAP 3 \u2014 VERF- EN MATERIAALADVIES: Geef 2-4 concrete suggesties voor "
    "verfkleuren, behang, of materiaal die bij dit palet passen. "
    "Vermeld steeds: winkel/merk, productnaam, richtprijs, en WAAROM het past.\n\n"
    "STAP 4 \u2014 STYLINGTIP: Geef 1 concrete stylingtip die de kleuren in de ruimte "
    "laat spreken \u2014 geen shopadvies, maar een tip over presentatie.\n\n"
    "ABSOLUTELY FORBIDDEN:\n"
    "\u2022 Geef GEEN design-historie, ontwerpernamen, jaartallen, museum-context.\n"
    "\u2022 Zoek NIET naar schade, reparaties of gebreken.\n"
    "\u2022 Geef GEEN productkoppelingen voor meubels (dat is purchase-intent).\n"
    "\u2022 Geef GEEN stappenplannen of DIY-instructies.\n"
    "\u2022 Als je een persoon, gezicht of dier ziet: stop en retourneer "
    "{\"error\": \"\u26a0\ufe0f HouseFix AI kan geen gezichten of dieren analyseren.\"}\n"
    "\u2022 Als de foto volledig ongerelateerd is (auto, eten, landschap): stop en retourneer "
    "{\"error\": \"\U0001f50d Dit is niet herkend als interieur- of designfoto.\"}\n\n"
    "ALLOWED verf- en materiaalmerken:\n"
    "Wanden/plafond: Histor, Sigma, Flexa, Sikkens, Farrow & Ball, Annie Sloan, "
    "Crown, Boss Paint, Levis, V33, ALABASTINE\n"
    "Hout/meubelverf: V33, Boell, Annie Sloan, Dicco, Seprim\n"
    "Behang: Eijffinger, Rasch, BN International, NLXL\n"
    "Vloeren: Quick-Step, Parketdiscounter, HORNBACH\n\n"
    "Return valid JSON with these keys:\n"
    "intent (altijd 'identify'),\n"
    "colors (lijst van 4-8 Nederlandse kleurnamen uit de foto, bv "
    "[\"saliegroen\", \"cr\u00e8me\", \"eiken\", \"koper\", \"antraciet\", \"taupe\"]),\n"
    "style (stijlbenaming in het Nederlands, bv 'Japandi / Scandinavian modern'),\n"
    "vibe (sfeer in 1-2 woorden, bv 'rustiek warm' of 'minimalistisch koel'),\n"
    "description (1 natuurlijke alinea die het kleurenpalet en de sfeer beschrijft, "
    "alsof je het aan een vriend uitlegt die binnenloopt. Welke kleuren vallen op? "
    "Welk gevoel geeft de combinatie?),\n"
    "paint_tips (lijst van 2-4 objecten met: store (winkel/merk), product "
    "(productnaam), price (richtprijs met \u20ac-teken, bv '\u20ac45,00 per liter'), "
    "why (waarom dit product past bij dit palet/in deze ruimte \u2014 1 zin)),\n"
    "styling_tip (1 korte, concrete stylingtip die kleuren laat spreken, "
    "bv 'Verwissel je witte kussens voor mosterdgele exemplaren \u2014 dat "
    "trekt het saliegroen van de muren naar voren'),\n"
    "confidence (high/medium/low \u2014 wees eerlijk. 'medium' met uitleg is beter "
    "dan 'high' zonder onderbouwing)."
)


# ── FIND ITEM PROMPT ──
FIND_ITEM_PROMPT = (
    "Je bent een ervaren interieur-stylist met oog voor designmeubels en interieurproducten. "
    "Een gebruiker heeft een foto gestuurd van een meubelstuk en wil PRECIES DIT MEUBEL of "
    "iets vergelijkbaars vinden om te kopen.\n\n"
    "Jouw taak is om het meubel te identificeren en 3-5 vergelijkbare alternatieven te geven "
    "die de gebruiker echt kan kopen. Wees specifiek: noem bestaande merken, winkels en "
    "realistische prijzen in euro's.\n\n"
    "STAP 1 Identificeer het meubel: Benoem precies wat je ziet: type meubel "
    "(eetkamerstoel, salontafel, designlamp, etc.), stijl (Scandinavisch, Art Deco, "
    "Industrieel, Japandi, Mid-Century, Modern, etc.), materiaal (eiken, zwart metaal, "
    "fluweel, etc.), en opvallende kenmerken.\n\n"
    "STAP 2 Bedenk 3-5 vergelijkbare meubels die echt bestaan bij bekende winkels. "
    "Varieer in prijsklasse zodat er voor elk budget iets bij zit.\n"
    "Per alternatief: name (productnaam NL), store (winkel/merk), price (realistisch in euro), "
    "url (realistische product-URL), why (1 zin waarom dit past bij het getoonde meubel), "
    "query (zoekterm voor catalogus).\n\n"
    "FORBIDDEN: geen schade/kleur/DIY-advies. Verzin geen producten of URLs. "
    "Als foto geen meubel is: error. Als foto gezicht/dier bevat: error.\n\n"
    "Return JSON: intent ('find_item'), object_type (korte benaming), "
    "alternatives (lijst 3-5 met name,store,price,url,why,query), "
    "styling_tip (1 korte tip), can_visualize (altijd false), "
    "confidence (high/medium/low)."
)

# ── PURCHASE PROMPT ──
PURCHASE_PROMPT = (
    "You are een high-end interieur- en designadviseur met oog voor kwaliteit. Een "
    "gebruiker heeft een foto gestuurd en wil weten welke producten hij/zij kan KOPEN.\n\n"
    "═══ KERNREGEL ═══\n"
    "Zoek eerst de BESTE VISUELE MATCH. Segmentatie komt daarna. "
    "Middenklasse en premium zijn VERBODEN voor budgetmerken.\n\n"
    "═══ SCENE-TYPE ROUTERING ═══\n"
    "CONTEXT bevat SCENE_TYPE. Kies het juiste pad:\n\n"
    "PAD A — object_closeup (foto van een specifiek object: vaas, lamp, stoel, tafel):\n"
    "  STAP 1: Identificeer het object exact: materiaal, stijl, kleur, afmeting.\n"
    "  STAP 2: Splits in TWEE complementaire aanbevelingen:\n"
    "    (a) EXACTE MATCH: Het product dat het meest op de foto lijkt.\n"
    "    (b) COMPOSITIE: Functionele items die een COMPOSITIE vormen met het object.\n"
    "  COMPOSITIEREGELS per object:\n"
    "    - VAAS → console/tafel/zuil (om op te staan), wandspot (om uit te lichten),\n"
    "      luxe dienblad of object in exact zelfde materiaal/stijl.\n"
    "      NOOIT: willekeurige kaarsen, kandelaars, planten die niet op de foto staan.\n"
    "    - STOEL → bijzettafel, vloerkleed, wandlamp (functioneel bij de stoel).\n"
    "    - LAMP → bijpassend meubel, dimmer (functioneel).\n"
    "    - TAFEL → stoelen, tafelstyling, centerpiece.\n"
    "    - KAST → wanddecoratie erboven, bijpassende accessoires ernaast.\n\n"
    "PAD B — complete_room (overzicht van een hele ruimte):\n"
    "  Identificeer ALLE zichtbare interieur-elementen. Prioriteer:\n"
    "  meubels → verf/behang → textiel → verlichting → accessoires → planten.\n"
    "  Geef per element het best passende product.\n\n"
    "PAD C — texture_detail (close-up van materiaal/textuur):\n"
    "  Focus op het specifieke materiaal (verf, behang, stof, vloer).\n"
    "  Adviseer producten die bij dit materiaal passen.\n\n"
    "═══ PRIJSSEGMENTATIE ═══\n"
    "Gebruik deze STRENGE regels per segment. OVERSCHRIJDING is niet toegestaan.\n\n"
    "BUDGET (€10 - €80):\n"
    "  Winkels: IKEA, HEMA, Action, Leen Bakker, Xenos\n"
    "  Dit is het enige segment waar budgetketens zijn toegestaan.\n"
    "  Eenvoudige, functionele alternatieven voor de look.\n\n"
    "MIDDENKLASSE (€80 - €500):\n"
    "  VERBODEN: IKEA, HEMA, Action, Leen Bakker, Xenos.\n"
    "  Toegestaan: Woonexpress, Intratuin, Karwei designlijn, VT Wonen webshop,\n"
    "    fonQ, designonline.nl, Westwing, BOL.com design, Kwantum designlijn,\n"
    "    JYSK designserie, H&M Home (alleen accessoires), Zara Home (design-lijn).\n"
    "  Dit is het HOOFDSEGMENT — hier zit de beste visuele match.\n"
    "  Producten moeten Kwaliteit uitstralen: massief hout, zuiver linnen, designermerken.\n\n"
    "PREMIUM (€500 - €2.000+):\n"
    "  VERBODEN: ALLE budget- en retailketens (IKEA, HEMA, Action, Leen Bakker,\n"
    "    Woonexpress, Karwei, JYSK, Kwantum, HEMA Home, Zara Home).\n"
    "  Toegestaan: De Bommel exclusief, Intratuin designer, MOOOI, Artifort,\n"
    "    &Tradition, Hay, Vitra, Eichholtz, exclusieve designwinkels, galeries.\n"
    "  Dit segment is voor designklassiekers, limited editions, ambachtelijk werk.\n\n"
    "═══ COMPOSITIELOGICA ═══\n"
    "Een complementair product is ALLEEN logisch als het:\n"
    "1. Een FUNCTIE heeft ten opzichte van het hoofdobject\n"
    "   - JUIST: 'Deze eiken console accentueert de vaas door hoogte en contrast'\n"
    "   - FOUT: 'Deze kaars staat gezellig naast de vaas'\n"
    "2. In dezelfde STIJL is als het hoofdobject (Japandi → eiken, industrieel → metaal)\n"
    "3. Een PRIJS heeft die past bij het object (geen €9,99 product naast een €200 vaas)\n"
    "4. Een VISUELE REDEN heeft in de compositie\n"
    "   - JUIST: 'Deze wandspot versterkt de sculpturale kwaliteit van de vaas'\n"
    "   - FOUT: 'Dit past er wel bij'\n\n"
    "ABSOLUTELY FORBIDDEN:\n"
    "• Geef GEEN stijleducatie, designgeschiedenis of stijlcontext.\n"
    "• Geef GEEN identificatie van objecten (dat is een andere intentie).\n"
    "• Geef GEEN reparatie- of klusadvies.\n"
    "• Zoek NIET naar schade, gebreken of slijtage.\n"
    "• Gebruik NOOIT IKEA, HEMA, Action of Leen Bakker in middenklasse of premium.\n\n"
    "Return valid JSON with these keys:\n"
    "intent (altijd 'purchase'),\n"
    "object_type (korte benaming van de ruimte of compositie, bv. 'Japandi zithoek met eiken salontafel en rotan fauteuil'),\n"
    "description (2-3 zinnen in Nederlands. Beschrijf wat je ziet en wat de gebruiker kan kopen om deze look te realiseren. Warm en praktisch.),\n"
    "segments (object met 3 keys: 'budget', 'middenklasse', 'premium'. Elk is een array van product-objecten. Elk product-object:\n"
    "  - category: 'meubel'|'verf'|'accessoire'|'textiel'|'verlichting'|'plant'|'wanddecoratie'\n"
    "  - name: Exacte productnaam + winkel, bv. 'Woonexpress eiken salontafel 100×60 cm conische poten'\n"
    "  - price: prijsindicatie, bv. '€349'\n"
    "  - store: winkelnaam, bv. 'Woonexpress'\n"
    "  - why: waarom dit product de beste match is. Visueel argument.\n"
    "  - visual_match: 1-10 integer. Hoe goed matcht dit product visueel met de foto?\n"
    "  - visual: object met color_palette (array 2-3 hex codes), mood (warm|fris|stoer|rustig), style_tag (scandinavisch|japandi|industrieel|boho|modern),\n"
    "  - position: center|left|right|top|floor — waar in de compositie dit product hoort,\n"
    "  - featured: boolean (true voor hoofdproduct, max 1 per segment),\n"
    "  - priority: 1 (essentieel), 2 (belangrijk), 3 (optioneel)\n"
    "  - query: zoekquery voor de productcatalogus. Combineer product_type + style_tag + kleur/materiaal, "
    "bv. 'eiken salontafel 100x60 scandinavisch naturel' of 'rotan fauteuil naturel boho'. "
    "Gebruik Nederlandse termen. Geen winkelnaam in de query.\n"
    "),\n"
    "colors (array van verfkleuren als er geschilderde muren te zien zijn. Elk: name, exact (kleurcode), finish, segment),\n"
    "materials (array van materialen voor DIY-elementen. Elk: name, segment, price, where),\n"
    "total_estimate (totale prijs voor middenklasse-selectie, bv. '€650 - €1.200'),\n"
    "shopping_list (array van 5-8 strings: compacte, afvinkbare items uit middenklasse. Elk: 'productnaam — winkel, prijs'),\n"
    "confidence (high/medium/low)."
)

ORIENTATION_PROMPT = (
    "You are a warm, betrokken interieuradviseur. Een gebruiker stuurt je een foto "
    "van zijn/haar interieur en wil een eerste indruk.\n\n"
    "Jouw taak is om een ORIËNTATIE te geven — dit is stap 1 van een gesprek. "
    "Je geeft NOG GEEN shopadvies, kleuradvies, stappenplan of stylingtips. "
    "Alleen een warme reactie en herkenning van de stijl.\n\n"
    "STAP 0 — SCENE BEPALING: Kijk eerst naar de foto en bepaal wat voor beeld dit is:\n"
    "  - complete_room: Een overzicht van een hele ruimte (woonkamer, slaapkamer, keuken) met meerdere meubels, objecten en voldoende context om de stijl te bepalen.\n"
    "  - object_closeup: Een close-up van een specifiek object (vaas, lamp, stoel, tafel) met beperkte context. De achtergrond is zichtbaar maar er is geen complete ruimte.\n"
    "  - texture_detail: Een detailopname van een materiaal of textuur (houtnerf, stof, verf) zonder herkenbare objecten of ruimte.\n"
    "  - unclear: Niet duidelijk of het om interieur gaat, of de foto is te beperkt voor een zinvolle stijlanalyse.\n\n"
    "Pas je hele analyse aan op basis van scene_type. Bij object_closeup en texture_detail benoem je het object of materiaal, niet een complete ruimte.\n\n"
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
    "user_intent (bepaal de intentie van de gebruiker op basis van de foto. "
    "Kies uit een van deze waarden:\n"
    "  - 'identify': Het hoofdonderwerp is één object, ingelijst met aandacht voor het object zelf. "
    "De gebruiker wil weten: wat is dit, welk ontwerp, welk materiaal, welke stijl?\n"
    "  - 'purchase': De foto toont een duidelijk herkenbare interieursituatie met meerdere "
    "zichtbare interieur-elementen (meubels, verfkleuren, materialen, stoffen, verlichting, "
    "accessoires) die de gebruiker waarschijnlijk wil namaken of kopen. "
    "Dit geldt voor complete_room scenes waar je specifieke producten kunt aanwijzen.\n"
    "  - (leeg): Bij alle andere situaties, of bij twijfel. "
    "Laat leeg. De gebruiker kiest dan zelf.\n"
    "Alleen 'identify', 'purchase' of leeg — geen andere waarden.\n"
    "),\n"
    "scene_type (een van: 'complete_room', 'object_closeup', 'texture_detail', 'unclear' — bepaal op basis van de foto),\n"
    "style (korte stijlbenaming in het Nederlands, 1-3 woorden, e.g. 'Scandinavisch' or 'Modern industrieel'. Bij object_closeup: de stijl van het object. Bij texture_detail: de stijl waarbij dit materiaal past.),\n"
    "reaction (1 warme zin als eerste reactie, natuurlijk en enthousiast, "
    "alsof je tegen een vriend praat, e.g. 'Wat een prachtige, lichte kamer!' of 'Wat een mooie vaas — die past perfect bij een Scandinavisch interieur!'),\n"
    "style_explanation (1-2 zinnen over waarom deze stijl werkt — welke kleuren, "
    "materialen en elementen de sfeer bepalen. Bij object_closeup: leg uit hoe dit object in een interieur past en welke stijl het versterkt.),\n"
    "vibe (1 woord dat de sfeer beschrijft, e.g. 'rustig', 'speels', 'luxe', 'warm', 'fris'),\n"
    "confidence (high/medium/low — wees eerlijk maar geef altijd je beste gok).\n"
    "Always return ALL 7 fields."
)

# ── Session Cache for multi-step conversation ──
SESSION_CACHE = {}
SESSION_TTL = 3600  # 1 hour

# ── Response Cache (keyed by image hash to avoid redundant GPT calls) ──
RESPONSE_CACHE = {}
RESPONSE_CACHE_TTL = 7200  # 2 hours

def image_hash(image_b64):
    """Deterministic short hash from a base64 image string."""
    return hashlib.sha256(image_b64[:2000].encode()).hexdigest()[:16]

def cache_key(mode, step, image_b64, goal=""):
    """Build a cache key from mode + step + image hash + optional goal."""
    h = image_hash(image_b64)
    return f"{mode}:{step}:{h}:{goal}"

def get_cached_response(key):
    """Return cached response if valid, else None."""
    entry = RESPONSE_CACHE.get(key)
    if entry and time.time() - entry['created_at'] < RESPONSE_CACHE_TTL:
        return entry['data']
    return None

def set_cached_response(key, data):
    """Store a response in the cache."""
    RESPONSE_CACHE[key] = {'data': data, 'created_at': time.time()}

def cleanup_cache():
    """Remove expired cache entries."""
    now = time.time()
    expired = [k for k, v in RESPONSE_CACHE.items()
               if now - v['created_at'] > RESPONSE_CACHE_TTL]
    for k in expired:
        del RESPONSE_CACHE[k]

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
    {"scene_type": "complete_room", "style": "Scandinavisch", "reaction": "Wat een prachtige, lichte ruimte!", "style_explanation": "Deze stijl draait om eenvoud, natuurlijke materialen en licht. Wit houtwerk, lichte meubels en groene planten zorgen voor een rustige, frisse uitstraling.", "vibe": "rustig", "confidence": "high"},
    {"scene_type": "complete_room", "style": "Modern industrieel", "reaction": "Wow, wat een gave industriële uitstraling!", "style_explanation": "Ruwe materialen zoals beton en staal, gecombineerd met warm hout en leer. Open ruimtes met hoge plafonds en grote ramen kenmerken deze stijl.", "vibe": "stoer", "confidence": "high"},
    {"scene_type": "complete_room", "style": "Japandi", "reaction": "Wat een serene, minimalistische schoonheid!", "style_explanation": "De perfecte balans tussen Japanse eenvoud en Scandinavische gezelligheid. Natuurlijke materialen, neutrale kleuren en strakke lijnen creëren rust.", "vibe": "harmonisch", "confidence": "medium"},
    {"scene_type": "complete_room", "style": "Bohemian", "reaction": "Wat een heerlijk eclectische mix!", "style_explanation": "Kleurrijke texturen, wereldse accessoires en een ontspannen sfeer. Veel planten, kussens en unieke vondsten maken deze stijl persoonlijk en warm.", "vibe": "vrij", "confidence": "medium"},
    {"scene_type": "complete_room", "style": "Moderne Scandinavisch", "reaction": "Wat een prachtige, lichte ruimte! De balans tussen hout en wit is perfect.", "style_explanation": "Deze stijl draait om eenvoud, natuurlijke materialen en licht. Wit houtwerk, lichte meubels en groene planten zorgen voor een rustige, frisse uitstraling. De houten vloer en wollen accessoires geven warmte.", "vibe": "fris", "confidence": "high", "user_intent": "purchase"},
    {"scene_type": "complete_room", "style": "Japandi minimalisme", "reaction": "Wat een serene schoonheid — elk detail is bewust gekozen.", "style_explanation": "Japanse eenvoud ontmoet Scandinavische hygge. Eiken meubels, neutrale tinten en organische vormen. De rotan accenten en keramiek geven textuur.", "vibe": "harmonisch", "confidence": "medium", "user_intent": "purchase"},
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

# ── Fallback identify data ──
FALLBACK_IDENTIFY = [
    {
        "intent": "identify",
        "object_type": "Keramieken vaas",
        "identification": {
            "type": "Handgedraaide keramieken vaas met mat saliegroen glazuur",
            "materials": ["keramiek", "mat saliegroen glazuur"],
            "style": "Japandi / Wabi-sabi",
            "design_period": "1960-1980, studio pottery — vermoedelijk Scandinavisch of Japans",
            "designer_hint": "De organische vorm en matte glazuur doen denken aan Lucie Rie of Katherine Pleydell-Bouverie",
            "key_features": [
                "organische, asymmetrische vorm",
                "subtiele variatie in glazuurdikte",
                "ongelakte bodem (teken van ambachtelijk werk)",
                "matte, niet-reflecterende afwerking"
            ],
            "why_special": "De variatie in glazuurdikte maakt elke vaas uniek — dit is het kenmerk van echt ambachtelijk werk, niet van serieproductie."
        },
        "style_context": "Deze vaas past perfect in een Japandi of Wabi-sabi interieur, waar imperfectie en natuurlijke materialen centraal staan. Ook in een Scandinavian modern interieur voegt het een organisch contrast toe aan strakke lijnen.",
        "description": "Wat een prachtig exemplaar! Dit is een handgedraaide keramieken vaas met een mat saliegroen glazuur dat prachtig varieert in dikte — zie je hoe het licht erin speelt? Die onregelmatigheid is geen fout, het is het kenmerk van echt handwerk. De organische, bijna asymmetrische vorm verraadt de invloed van Wabi-sabi, de Japanse filosofie die schoonheid ziet in imperfectie. Dit is geen serieproductie — dit is iemands ambacht, met liefde gemaakt aan een draaischijf. Een vaas als deze vertelt een verhaal van geduld en meesterschap.",
        "styling_tip": "Zet er een tak bloeiende kweepeer in voor een Wabi-sabi compositie — de knikken en vormen van de tak versterken de organische kwaliteit van de vaas.",
        "confidence": "high"
    },
    {
        "intent": "identify",
        "object_type": "Designstoel",
        "identification": {
            "type": "Iconische eetkamerstoel met gevormd hout en conische poten",
            "materials": ["gevormd fineerhout (eiken)", "chromen poten"],
            "style": "Mid-Century Modern / Scandinavian modern",
            "design_period": "Jaren 1950-1960, hoogtepunt van de Deense designgolf",
            "designer_hint": "Sterk verwant aan ontwerpen van Arne Jacobsen (Series 7) of Hans Wegner (Wishbone). Het gebruik van gevormd hout is typerend voor de Deense meubeltraditie.",
            "key_features": [
                "driedimensionaal gevormd fineer (zitvlak + rugleuning uit één stuk)",
                "conische, taps toelopende chromen poten",
                "ergonomische curve die het lichaam omarmt",
                "tijdloze proporties — even breed als hoog"
            ],
            "why_special": "Een stoel als deze heeft zijn vorm niet aan een computer te danken, maar aan jaren van experimenteren met fineerbuigen — een techniek die Deense ontwerpers in de jaren '50 tot perfectie brachten."
        },
        "style_context": "Deze stoel is een icoon van het Scandinavian modern design uit de jaren '50 en '60. Hij past in elk interieur dat ruimte geeft aan tijdloze vormgeving — van een minimalistisch Japandi tot een eclectische mix met industriële elementen.",
        "description": "Wat een prachtig stuk design! Dit is een eetkamerstoel in de beste traditie van Deens meubeldesign. Het opvallendste kenmerk is de gebogen rugleuning en het zitvlak, gemaakt uit één stuk gevormd fineerhout — een techniek die in de jaren '50 werd geperfectioneerd door ontwerpers als Arne Jacobsen. De conische chromen poten geven de stoel een bijna zwevend profiel. Wat deze stoel bijzonder maakt: hij is zowel comfortabel als sculpturaal. Hij nodigt uit om te gaan zitten, maar is ook een lust voor het oog als je eromheen loopt. Dit is design dat functioneel is zonder zijn schoonheid te verliezen.",
        "styling_tip": "Combineer met een eenvoudige eiken tafel en een hanglamp met een zwart snoer — dan komt de sculpturale kwaliteit van de stoel het beste tot zijn recht.",
        "confidence": "high"
    },
    {
        "intent": "identify",
        "object_type": "Tafellamp",
        "identification": {
            "type": "Minimalistische tafellamp met kegelvormige kap en dunne metalen arm",
            "materials": ["metaal (gelakt staal of aluminium)", "textiel bekleding op kap"],
            "style": "Bauhaus / Functionalistisch / Modernistisch",
            "design_period": "Jaren 1930-1960, geïnspireerd op Bauhaus-principes van 'vorm volgt functie'",
            "designer_hint": "De eenvoudige kegelvorm en verstelbare arm doen denken aan ontwerpen van Wilhelm Wagenfeld of Christian Dell, twee Duitse Bauhaus-ontwerpers die de basis legden voor modern lampenontwerp.",
            "key_features": [
                "verstelbare, draaibare arm voor gerichte verlichting",
                "kegelvormige kap die het licht bundelt",
                "minimalistische vorm — geen overbodige decoratie",
                "balans tussen functie en esthetiek: elk onderdeel heeft een doel"
            ],
            "why_special": "Deze lamp is een zuivere uitdrukking van 'vorm volgt functie': er is geen onderdeel dat niet functioneel is. Die ontwerpdiscipline is zeldzaam en tijdloos."
        },
        "style_context": "Een lamp als deze is even thuis op een bureau in een modernistisch interieur als op een nachtkastje in een Scandinavische slaapkamer. Het strakke, functionele ontwerp past bij elk interieur dat waarde hecht aan heldere lijnen en eerlijke materialen.",
        "description": "Dit is een prachtig voorbeeld van modernistisch lampenontwerp — en wat mij betreft een van de zuiverste vormen van design die er bestaat. De kegelvormige kap, de dunne metalen arm, de eenvoudige voet: alles aan deze lamp heeft een functie, niets is decoratie. Dat is het Bauhaus-principe in zijn puurste vorm. Wat ik bijzonder vind aan dit ontwerp is de manier waarop het licht wordt gemanipuleerd: de kap bundelt het licht naar beneden, terwijl de metalen arm het mogelijk maakt om de lichtbron precies te richten waar je het nodig hebt. Functioneel, maar ook esthetisch — want de lamp zelf trekt de aandacht, niet alleen het licht dat hij geeft.",
        "styling_tip": "Zet hem op een donker houten bureau met een open boek ernaast — dan wordt de lamp zelf een stilleven, niet alleen een lichtbron.",
        "confidence": "medium"
    }
]

# ── Fallback purchase data (3 voorbeelden — premium prijsniveau) ──
FALLBACK_PURCHASE = [
    {
        "intent": "purchase",
        "object_type": "Scandinavisch-Japandi zithoek met eiken salontafel, rotan fauteuil en linnen accessoires",
        "description": "Een warme, lichte zithoek waar Scandinavische eenvoud en Japanse harmonie samenkomen. Massief eiken meubels, handgevlochten rotan en zuiver linnen bepalen de sfeer.",
        "segments": {
            "budget": [
                {
                    "category": "meubel",
                    "name": "IKEA LACK salontafel 90×55 cm wit",
                    "price": "€29,99",
                    "store": "IKEA",
                    "why": "Zelfde strakke vorm, lichte uitstraling — budgetalternatief.",
                    "visual_match": 5,
                    "priority": 1,
                    "visual": {
                        "color_palette": [
                            "#d4c5b5",
                            "#8a7a6a"
                        ],
                        "mood": "warm",
                        "style_tag": "modern"
                    },
                    "position": "center",
                    "featured": True,
                    "query": "lack salontafel 90×55 cm wit modern warm"
                },
                {
                    "category": "meubel",
                    "name": "HEMA rotan fauteuil naturel",
                    "price": "€149",
                    "store": "HEMA",
                    "why": "Rotan gevlochten stoel, zelfde materiaal en kleur.",
                    "visual_match": 6,
                    "priority": 1,
                    "visual": {
                        "color_palette": [
                            "#d4c5b5",
                            "#8a7a6a"
                        ],
                        "mood": "warm",
                        "style_tag": "scandinavisch"
                    },
                    "position": "left",
                    "featured": False,
                    "query": "rotan fauteuil naturel scandinavisch warm"
                }
            ],
            "middenklasse": [
                {
                    "category": "meubel",
                    "name": "Woonexpress eiken salontafel 100×60 cm conische poten",
                    "price": "€349",
                    "store": "Woonexpress",
                    "why": "Massief eiken blad, conische poten, naturel afwerking — exact de look.",
                    "visual_match": 9,
                    "priority": 1,
                    "visual": {
                        "color_palette": [
                            "#d4c5b5",
                            "#8a7a6a"
                        ],
                        "mood": "warm",
                        "style_tag": "scandinavisch"
                    },
                    "position": "center",
                    "featured": True,
                    "query": "eiken salontafel 100×60 cm conische poten scandinavisch warm"
                },
                {
                    "category": "meubel",
                    "name": "Intratuin handgevlochten rotan fauteuil naturel",
                    "price": "€499",
                    "store": "Intratuin",
                    "why": "Dik rotan vlechtwerk, armleuningen, met dik zitkussen — exact de fauteuil.",
                    "visual_match": 9,
                    "priority": 1,
                    "visual": {
                        "color_palette": [
                            "#d4c5b5",
                            "#8a7a6a"
                        ],
                        "mood": "warm",
                        "style_tag": "scandinavisch"
                    },
                    "position": "left",
                    "featured": False,
                    "query": "handgevlochten rotan fauteuil naturel scandinavisch warm"
                },
                {
                    "category": "textiel",
                    "name": "Westwing linnen kussen 50×50 cm saliegroen",
                    "price": "€79,95",
                    "store": "Westwing",
                    "why": "Zuiver linnen in saliegroen, zelfde textuur en kleur.",
                    "visual_match": 9,
                    "priority": 2,
                    "visual": {
                        "color_palette": [
                            "#c4b5a5",
                            "#e8ddd0"
                        ],
                        "mood": "warm",
                        "style_tag": "scandinavisch"
                    },
                    "position": "right",
                    "featured": False,
                    "query": "linnen kussen 50×50 cm saliegroen scandinavisch warm"
                },
                {
                    "category": "verlichting",
                    "name": "fonQ rotan hanglamp 45 cm naturel",
                    "price": "€129",
                    "store": "fonQ",
                    "why": "Grote rotan hanglamp, warm licht, natuurlijk accent.",
                    "visual_match": 8,
                    "priority": 3,
                    "visual": {
                        "color_palette": [
                            "#f5e6d0",
                            "#d4c5b5"
                        ],
                        "mood": "warm",
                        "style_tag": "scandinavisch"
                    },
                    "position": "top",
                    "featured": False,
                    "query": "rotan hanglamp 45 cm naturel scandinavisch warm"
                },
                {
                    "category": "meubel",
                    "name": "Woonexpress eiken bijzettafel 45×45 cm",
                    "price": "€189",
                    "store": "Woonexpress",
                    "why": "Massief eiken, past bij de salontafel.",
                    "visual_match": 8,
                    "priority": 2,
                    "visual": {
                        "color_palette": [
                            "#d4c5b5",
                            "#8a7a6a"
                        ],
                        "mood": "warm",
                        "style_tag": "scandinavisch"
                    },
                    "position": "floor",
                    "featured": False,
                    "query": "eiken bijzettafel 45×45 cm scandinavisch warm"
                }
            ],
            "premium": [
                {
                    "category": "meubel",
                    "name": "Eichholtz eiken salontafel 120×70 cm met marmeren blad",
                    "price": "€1.495",
                    "store": "Exclusieve designwinkel",
                    "why": "Luxe uitvoering met marmer, sculpturaal ontwerp.",
                    "visual_match": 8,
                    "priority": 1,
                    "visual": {
                        "color_palette": [
                            "#d4c5b5",
                            "#8a7a6a"
                        ],
                        "mood": "warm",
                        "style_tag": "scandinavisch"
                    },
                    "position": "center",
                    "featured": True,
                    "query": "eiken salontafel 120×70 cm met marmeren blad scandinavisch warm"
                },
                {
                    "category": "meubel",
                    "name": "Artifort rotan fauteuil 'F888' handgevlochten",
                    "price": "€1.895",
                    "store": "Artifort",
                    "why": "Designklassieker, handgevlochten, museumwaardig.",
                    "visual_match": 9,
                    "priority": 1,
                    "visual": {
                        "color_palette": [
                            "#d4c5b5",
                            "#8a7a6a"
                        ],
                        "mood": "warm",
                        "style_tag": "scandinavisch"
                    },
                    "position": "left",
                    "featured": False,
                    "query": "rotan fauteuil 'f888' handgevlochten scandinavisch warm"
                }
            ]
        },
        "materials": [
            {
                "name": "Eiken tafelblad massief 100×60 cm",
                "segment": "middenklasse",
                "price": "€349",
                "where": "Woonexpress"
            },
            {
                "name": "Rotan fauteuil handgevlochten",
                "segment": "middenklasse",
                "price": "€499",
                "where": "Intratuin"
            }
        ],
        "colors": [
            {
                "name": "Warm wit (muren)",
                "exact": "Histor Natuurwit 1201",
                "finish": "mat",
                "segment": "budget"
            },
            {
                "name": "Saliegroen (kussen)",
                "exact": "Flexa Salie 25.03",
                "finish": "mat",
                "segment": "middenklasse"
            }
        ],
        "total_estimate": "€850 - €1.600",
        "shopping_list": [
            "Eiken salontafel conisch — Woonexpress, €349",
            "Rotan fauteuil handgevlochten — Intratuin, €499",
            "Linnen kussen salie 50×50 — Westwing, €79,95",
            "Rotan hanglamp 45 cm — fonQ, €129",
            "Eiken bijzettafel — Woonexpress, €189"
        ],
        "confidence": "high"
    },
    {
        "intent": "purchase",
        "object_type": "Industriële eethoek met zwart stalen tafel, cognac lederen stoelen en betonlook",
        "description": "Een karaktervolle industriële eethoek. Zwart stalen onderstel met massief eiken blad, cognac lederen stoelen en een betonlook accentmuur. Robuust, warm en tijdloos.",
        "segments": {
            "budget": [
                {
                    "category": "meubel",
                    "name": "IKEA NORDVIKEN tafel 120×80 cm zwart",
                    "price": "€149",
                    "store": "IKEA",
                    "why": "Zwart onderstel, houten blad — zelfde silhouet.",
                    "visual_match": 5,
                    "priority": 1,
                    "visual": {
                        "color_palette": [
                            "#4a4a4a",
                            "#6a6a6a"
                        ],
                        "mood": "stoer",
                        "style_tag": "industrieel"
                    },
                    "position": "center",
                    "featured": True,
                    "query": "nordviken tafel 120×80 cm zwart industrieel stoer"
                },
                {
                    "category": "meubel",
                    "name": "JYSK eetkamerstoel zwart kunstleer",
                    "price": "€79,99",
                    "store": "JYSK",
                    "why": "Zwarte stoel met kunstleren zitting.",
                    "visual_match": 5,
                    "priority": 1,
                    "visual": {
                        "color_palette": [
                            "#4a4a4a",
                            "#6a6a6a"
                        ],
                        "mood": "stoer",
                        "style_tag": "industrieel"
                    },
                    "position": "left",
                    "featured": False,
                    "query": "eetkamerstoel zwart kunstleer industrieel stoer"
                }
            ],
            "middenklasse": [
                {
                    "category": "meubel",
                    "name": "Woonexpress eettafel zwart metaal + eiken blad 200×90 cm",
                    "price": "€699",
                    "store": "Woonexpress",
                    "why": "Zwart stalen onderstel, massief eiken blad — exact de industriële tafellook.",
                    "visual_match": 9,
                    "priority": 1,
                    "visual": {
                        "color_palette": [
                            "#d4c5b5",
                            "#8a7a6a"
                        ],
                        "mood": "warm",
                        "style_tag": "scandinavisch"
                    },
                    "position": "center",
                    "featured": True,
                    "query": "eettafel zwart metaal + eiken blad 200×90 cm scandinavisch warm"
                },
                {
                    "category": "meubel",
                    "name": "Intratuin eetkamerstoel cognac leder 2-pack",
                    "price": "€599",
                    "store": "Intratuin",
                    "why": "Cognac lederen stoel, metalen onderstel — identiek aan de foto.",
                    "visual_match": 9,
                    "priority": 1,
                    "visual": {
                        "color_palette": [
                            "#4a4a4a",
                            "#6a6a6a"
                        ],
                        "mood": "stoer",
                        "style_tag": "industrieel"
                    },
                    "position": "left",
                    "featured": False,
                    "query": "eetkamerstoel cognac leder 2-pack industrieel stoer"
                },
                {
                    "category": "verlichting",
                    "name": "fonQ zwarte industriële hanglamp metaal",
                    "price": "€89,95",
                    "store": "fonQ",
                    "why": "Zwarte metalen hanglamp met industriële uitstraling.",
                    "visual_match": 9,
                    "priority": 2,
                    "visual": {
                        "color_palette": [
                            "#f5e6d0",
                            "#d4c5b5"
                        ],
                        "mood": "stoer",
                        "style_tag": "industrieel"
                    },
                    "position": "right",
                    "featured": False,
                    "query": "zwarte industriële hanglamp metaal industrieel stoer"
                },
                {
                    "category": "wanddecoratie",
                    "name": "VT Wonen betonlook wandpanel 120×80 cm",
                    "price": "€149",
                    "store": "VT Wonen webshop",
                    "why": "Betonlook paneel voor de accentmuur.",
                    "visual_match": 8,
                    "priority": 2,
                    "visual": {
                        "color_palette": [
                            "#e8ddd0",
                            "#d4c5b5"
                        ],
                        "mood": "warm",
                        "style_tag": "modern"
                    },
                    "position": "top",
                    "featured": False,
                    "query": "betonlook wandpanel 120×80 cm modern warm"
                }
            ],
            "premium": [
                {
                    "category": "meubel",
                    "name": "Eichholtz eettafel massief eiken met stalen onderstel 240×100 cm",
                    "price": "€2.495",
                    "store": "Eichholtz",
                    "why": "Massief eiken, handgelast stalen onderstel — design statement.",
                    "visual_match": 10,
                    "priority": 1,
                    "visual": {
                        "color_palette": [
                            "#d4c5b5",
                            "#8a7a6a"
                        ],
                        "mood": "warm",
                        "style_tag": "scandinavisch"
                    },
                    "position": "center",
                    "featured": True,
                    "query": "eettafel massief eiken met stalen onderstel 240×100 cm scandinavisch warm"
                },
                {
                    "category": "meubel",
                    "name": "Hay eetkamerstoel cognac leder 'About a Chair'",
                    "price": "€695",
                    "store": "Hay",
                    "why": "Designklassieker, cognac leder, metalen onderstel.",
                    "visual_match": 9,
                    "priority": 1,
                    "visual": {
                        "color_palette": [
                            "#4a4a4a",
                            "#6a6a6a"
                        ],
                        "mood": "stoer",
                        "style_tag": "industrieel"
                    },
                    "position": "left",
                    "featured": False,
                    "query": "eetkamerstoel cognac leder 'about a chair' industrieel stoer"
                }
            ]
        },
        "materials": [
            {
                "name": "Eiken tafelblad massief 200×90 cm",
                "segment": "middenklasse",
                "price": "€699",
                "where": "Woonexpress"
            },
            {
                "name": "Leder eetkamerstoel cognac 2-pack",
                "segment": "middenklasse",
                "price": "€599",
                "where": "Intratuin"
            },
            {
                "name": "Betonlook wandpanel",
                "segment": "middenklasse",
                "price": "€149",
                "where": "VT Wonen"
            }
        ],
        "colors": [
            {
                "name": "Zwart (meubels)",
                "exact": "Flexa Zwart Mat 90.01",
                "finish": "mat",
                "segment": "middenklasse"
            },
            {
                "name": "Betonlook grijs (muur)",
                "exact": "Histor Betonlook 30.02",
                "finish": "mat",
                "segment": "middenklasse"
            }
        ],
        "total_estimate": "€1.500 - €3.000",
        "shopping_list": [
            "Eettafel zwart metaal + eiken — Woonexpress, €699",
            "Eetkamerstoel cognac leder 2-pack — Intratuin, €599",
            "Zwarte hanglamp industrieel — fonQ, €89,95",
            "Betonlook wandpanel — VT Wonen, €149"
        ],
        "confidence": "high"
    },
    {
        "intent": "purchase",
        "object_type": "Bohemian slaapkamer met rotan hoofdbord, macramé en groene planten",
        "description": "Een warme, ontspannen slaapkamer met een breed rotan hoofdbord als middelpunt. Macramé wandkunst, zuiver linnen beddegoed en een grote vijgenboom creëren een natuurlijke, geborgen sfeer.",
        "segments": {
            "budget": [
                {
                    "category": "meubel",
                    "name": "HEMA rotan hoofdbord 140 cm",
                    "price": "€79,99",
                    "store": "HEMA",
                    "why": "Rotan hoofdbord, zelfde gevlochten look.",
                    "visual_match": 6,
                    "priority": 1,
                    "visual": {
                        "color_palette": [
                            "#d4c5b5",
                            "#8a7a6a"
                        ],
                        "mood": "warm",
                        "style_tag": "scandinavisch"
                    },
                    "position": "center",
                    "featured": True,
                    "query": "rotan hoofdbord 140 cm scandinavisch warm"
                },
                {
                    "category": "textiel",
                    "name": "IKEA LENDEARYLL linnen dekbedovertrek beige",
                    "price": "€19,99",
                    "store": "IKEA",
                    "why": "Linnen look, warme beige tint.",
                    "visual_match": 5,
                    "priority": 2,
                    "visual": {
                        "color_palette": [
                            "#c4b5a5",
                            "#e8ddd0"
                        ],
                        "mood": "warm",
                        "style_tag": "scandinavisch"
                    },
                    "position": "left",
                    "featured": False,
                    "query": "lendearyll linnen dekbedovertrek beige scandinavisch warm"
                }
            ],
            "middenklasse": [
                {
                    "category": "meubel",
                    "name": "Intratuin rotan hoofdbord 200 cm breed handgevlochten",
                    "price": "€399",
                    "store": "Intratuin",
                    "why": "Breed handgevlochten rotan hoofdbord — exact de look van de foto.",
                    "visual_match": 10,
                    "priority": 1,
                    "visual": {
                        "color_palette": [
                            "#d4c5b5",
                            "#8a7a6a"
                        ],
                        "mood": "warm",
                        "style_tag": "scandinavisch"
                    },
                    "position": "center",
                    "featured": True,
                    "query": "rotan hoofdbord 200 cm breed handgevlochten scandinavisch warm"
                },
                {
                    "category": "textiel",
                    "name": "Westwing linnen dekbedovertrek ivory 240×220 cm",
                    "price": "€149",
                    "store": "Westwing",
                    "why": "Zuiver linnen, ivory, zelfde textuur en kleur.",
                    "visual_match": 10,
                    "priority": 1,
                    "visual": {
                        "color_palette": [
                            "#c4b5a5",
                            "#e8ddd0"
                        ],
                        "mood": "warm",
                        "style_tag": "scandinavisch"
                    },
                    "position": "left",
                    "featured": False,
                    "query": "linnen dekbedovertrek ivory 240×220 cm scandinavisch warm"
                },
                {
                    "category": "wanddecoratie",
                    "name": "VT Wonen macramé wandkleed 120×80 cm handgeknoopt",
                    "price": "€89,95",
                    "store": "VT Wonen webshop",
                    "why": "Macramé wandkleed, handgeknoopt, naturel.",
                    "visual_match": 8,
                    "priority": 2,
                    "visual": {
                        "color_palette": [
                            "#e8ddd0",
                            "#d4c5b5"
                        ],
                        "mood": "fris",
                        "style_tag": "boho"
                    },
                    "position": "right",
                    "featured": False,
                    "query": "macramé wandkleed 120×80 cm handgeknoopt boho fris"
                },
                {
                    "category": "plant",
                    "name": "Intratuin vijgenboom 180 cm",
                    "price": "€89,95",
                    "store": "Intratuin",
                    "why": "Grote vijgenboom, weelderig groen.",
                    "visual_match": 9,
                    "priority": 2,
                    "visual": {
                        "color_palette": [
                            "#7a9b6a",
                            "#5a7a4a"
                        ],
                        "mood": "fris",
                        "style_tag": "boho"
                    },
                    "position": "top",
                    "featured": False,
                    "query": "vijgenboom 180 cm boho fris"
                },
                {
                    "category": "accessoire",
                    "name": "fonQ rotan bijzettafel 50 cm rond",
                    "price": "€119",
                    "store": "fonQ",
                    "why": "Rotan bijzettafel, past bij het hoofdbord.",
                    "visual_match": 8,
                    "priority": 3,
                    "visual": {
                        "color_palette": [
                            "#d4c5b5",
                            "#c4b5a5"
                        ],
                        "mood": "warm",
                        "style_tag": "scandinavisch"
                    },
                    "position": "floor",
                    "featured": False,
                    "query": "rotan bijzettafel 50 cm rond scandinavisch warm"
                }
            ],
            "premium": [
                {
                    "category": "meubel",
                    "name": "De Bommel rotan hoofdbord 220 cm handgevlochten massief frame",
                    "price": "€895",
                    "store": "De Bommel",
                    "why": "Handgevlochten rotan, massief eiken frame, uniek exemplaar.",
                    "visual_match": 10,
                    "priority": 1,
                    "visual": {
                        "color_palette": [
                            "#d4c5b5",
                            "#8a7a6a"
                        ],
                        "mood": "warm",
                        "style_tag": "scandinavisch"
                    },
                    "position": "center",
                    "featured": True,
                    "query": "rotan hoofdbord 220 cm handgevlochten massief frame scandinavisch warm"
                },
                {
                    "category": "textiel",
                    "name": "De Bommel Belgisch linnen dekbedovertrek ivory 260×240 cm",
                    "price": "€299",
                    "store": "De Bommel",
                    "why": "Belgisch linnen, hoogste kwaliteit, wordt zachter met elke wasbeurt.",
                    "visual_match": 10,
                    "priority": 1,
                    "visual": {
                        "color_palette": [
                            "#c4b5a5",
                            "#e8ddd0"
                        ],
                        "mood": "warm",
                        "style_tag": "scandinavisch"
                    },
                    "position": "left",
                    "featured": False,
                    "query": "belgisch linnen dekbedovertrek ivory 260×240 cm scandinavisch warm"
                }
            ]
        },
        "materials": [
            {
                "name": "Rotan hoofdbord 200 cm handgevlochten",
                "segment": "middenklasse",
                "price": "€399",
                "where": "Intratuin"
            },
            {
                "name": "Linnen dekbedovertrek ivory",
                "segment": "middenklasse",
                "price": "€149",
                "where": "Westwing"
            }
        ],
        "colors": [
            {
                "name": "Ivory (beddegoed)",
                "exact": "Flexa Naturel Mat 10.01",
                "finish": "mat",
                "segment": "middenklasse"
            },
            {
                "name": "Rotan naturel",
                "exact": "Flexa Rotan Mat 15.02",
                "finish": "mat",
                "segment": "middenklasse"
            }
        ],
        "total_estimate": "€650 - €1.600",
        "shopping_list": [
            "Rotan hoofdbord 200 cm — Intratuin, €399",
            "Linnen dekbedovertrek ivory — Westwing, €149",
            "Macramé wandkleed 120×80 — VT Wonen, €89,95",
            "Vijgenboom 180 cm — Intratuin, €89,95",
            "Rotan bijzettafel — fonQ, €119"
        ],
        "confidence": "high"
    }
]

# Initialize product catalog (after FALLBACK_PURCHASE is defined)
init_catalog()

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/health")
def health():
    try:
        n = int(len(search_catalog(limit=999)))
    except Exception:
        n = 0
    return jsonify({"status": "ok", "service": "HouseFix AI", "catalog_products": n})


@app.route("/api/products")
def list_catalog_products():
    q = request.args.get('q', '').strip() or None
    store = request.args.get('store', '').strip() or None
    segment = request.args.get('segment', '').strip() or None
    category = request.args.get('category', '').strip() or None
    try:
        limit = max(1, min(int(request.args.get('limit', 5)), 10))
    except ValueError:
        limit = 5
    products = search_catalog(q=q, store=store, segment=segment, category=category, limit=limit)
    return jsonify({"products": products, "total": len(products), "query": q or ""})


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

    # If no API key, check cache first, then fallback
    if not OPENAI_API_KEY:
        ck = cache_key(mode, step or "", image_base64, data.get("goal", "") + ":" + data.get("user_intent", ""))
        cached = get_cached_response(ck)
        if cached:
            cached["_cached"] = True
            return jsonify(cached)

        if mode == "inspiration" and step == "orient":
            fallback = random.choice(FALLBACK_ORIENT)
            session_id = create_session(image_base64, fallback)
            return jsonify({"orient": fallback, "session_id": session_id, "is_fallback": True})
        elif mode == "inspiration" and step == "advise":
            if not data.get("session_id"):
                data["session_id"] = ""
            user_intent = data.get("user_intent", "")
            if user_intent == "identify":
                result = random.choice(FALLBACK_IDENTIFY)
            elif user_intent == "purchase":
                # Use user_answers to select matching segment from a random scenario
                fallback_scenario = random.choice(FALLBACK_PURCHASE)
                ua = data.get("user_answers", {})
                budget = ua.get("budget", "design")
                if budget != "design":
                    seg_map = {"budget": "budget", "luxe": "premium"}
                    preferred_seg = seg_map.get(budget, "middenklasse")
                    fallback_scenario["best_seg"] = preferred_seg
                result = fallback_scenario
            else:
                result = random.choice(FALLBACK_INSPIRATION)
            result["is_fallback"] = True
            return jsonify(result)
        result = random.choice(FALLBACK_ISSUES)
        result["is_fallback"] = True
        return jsonify(result)

    # ── INSPIRATION MODE: STEP 1 — Orientation ──
    if mode == "inspiration" and step == "orient":
        # Check cache before calling GPT
        ock = cache_key(mode, "orient", image_base64)
        ocached = get_cached_response(ock)
        if ocached:
            session_id = create_session(image_base64, ocached)
            return jsonify({"orient": ocached, "session_id": session_id, "_cached": True})

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
                # Store in response cache for future requests
                set_cached_response(ock, parsed)
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
        request_intent = data.get("user_intent", "")
        user_intent = request_intent
        context_parts = []
        if session:
            orient = session.get('orient', {})
            scene_type = orient.get('scene_type', 'complete_room')
            request_intent = data.get("user_intent", "")
            user_intent = request_intent if request_intent else orient.get("user_intent", "")
            context_parts.append(f"SCENE_TYPE: {scene_type}")
            context_parts.append(f"USER_INTENT: {user_intent}")
            context_parts.append(f"Eerste indruk van deze ruimte: {orient.get('style', 'onbekend')} — {orient.get('style_explanation', '')}")
            context_parts.append(f"Sfeer: {orient.get('vibe', '')}")
            # Use stored image
            image_base64 = session.get('image', image_base64)
        else:
            context_parts.append("Geen eerdere sessie gevonden — geef advies op basis van de foto alleen.")

        if goal:
            context_parts.append(f"DOEL VAN DE GEBRUIKER: {goal}")

        # ── Inject user_answers for purchase intent ──
        user_answers = data.get("user_answers", {})
        if user_intent == "purchase" and user_answers:
            ua = user_answers
            context_parts.append("\n═══ GEBRUIKERSPARAMETERS (harde constraints) ═══")
            focus_map = {"exact": "EXACTE MATCH: visual_match 9-10, alleen producten die bijna identiek zijn aan de foto", "style": "STIJL_MATCH: visual_match 6-8, zelfde stijl maar andere uitvoering, breder productaanbod"}
            context_parts.append(f"FOCUS: {focus_map.get(ua.get('focus',''), 'EXACTE MATCH')}")
            scale_map = {"item": "ALLEEN ITEM: alleen het hoofdproduct, geen complementaire items, max 1-2 producten", "composition": "COMPOSITIE: hoofdproduct + 2-4 functionele complementen die een logische compositie vormen"}
            context_parts.append(f"SCHAAL: {scale_map.get(ua.get('scale',''), 'COMPOSITIE')}")
            space_map = {"existing": "BESTAAND INTERIEUR: kleuren, materialen en stijl moeten harmoniëren met de bestaande interieurcontext op de foto. Geen complete stijlbreuk.", "new": "VRIJ ONTWERP: AI mag een compleet nieuw stijlbeeld kiezen met nieuwe kleuren, materialen en sfeer."}
            context_parts.append(f"RUIMTE: {space_map.get(ua.get('space',''), 'BESTAAND INTERIEUR')}")
            styling_map = {"minimal": "MINIMALISTISCH: alleen de essentie, 1-2 kernproducten, geen accessoires, strak en functioneel", "rich": "RIJK & SFEERVOL: 4-7 producten inclusief accessoires, textiel, verlichting, decoratie"}
            context_parts.append(f"STYLING: {styling_map.get(ua.get('styling',''), 'RIJK & SFEERVOL')}")
            budget_val = ua.get('budget', 'design')
            if budget_val == "budget":
                context_parts.append("BUDGET_SEGMENT: BUDGET. MAX €80 per product. Alleen winkels: IKEA, HEMA, Action, JYSK, Leen Bakker, Xenos. VERBODEN: alle designmerken. Eenvoudige functionele producten.")
            elif budget_val == "design":
                context_parts.append("BUDGET_SEGMENT: TOEGANKELIJK DESIGN. €80-€500 per product. VERBODEN: IKEA, HEMA, Action, JYSK, Leen Bakker, Xenos. Toegestaan: Woonexpress, Intratuin, Westwing, fonQ, VT Wonen. Kwaliteit: massief hout, zuiver linnen, designermerken.")
            elif budget_val == "luxe":
                context_parts.append("BUDGET_SEGMENT: EXCLUSIEVE LUXE. MIN €500 per product, geen bovengrens. VERBODEN: ALLE retailketens (IKEA, HEMA, Woonexpress, Intratuin standaard, Karwei). Toegestaan: Eichholtz, Artifort, Hay, Vitra, MOOOI, De Bommel exclusief. Designklassiekers, limited editions, ambachtelijk.")
            context_parts.append("═══ EINDE GEBRUIKERSPARAMETERS ═══")

        user_context = "\n".join(context_parts)

        # Check cache before calling GPT
        ack = cache_key(mode, "advise", image_base64, f"{goal}:{request_intent}:{json.dumps(data.get('user_answers',{}), sort_keys=True)}")
        acached = get_cached_response(ack)
        if acached:
            return jsonify(acached)

        try:
            client = OpenAI(api_key=OPENAI_API_KEY)

            # Select prompt based on user intent
            if user_intent == "identify":
                base_prompt = COLOR_PALETTE_PROMPT
                system_message = (
                    "Je bent een interieurstylist die kleurenpaletten analyseert. "
                    "Gebruik de foto om een compleet kleuradvies te geven."
                )
            elif user_intent == "purchase":
                base_prompt = PURCHASE_PROMPT
                system_message = (
                    "Je bent een praktische interieuradviseur voor aankoopadvies. "
                    "Gebruik de context om productadvies op maat te geven."
                )
            else:
                base_prompt = INSPIRATION_PROMPT
                system_message = (
                    "Gebruik deze context om je advies te personaliseren. "
                    "Het doel van de gebruiker is hierboven vermeld — pas je hele advies daarop aan."
                )

            purchase_context = user_context if user_intent == "purchase" else ""
            full_prompt = (
                f"\n[[HARD CONSTRAINTS]]\n{purchase_context}\n[[END HARD CONSTRAINTS]]\n\n"
                f"{base_prompt}\n\n{system_message}"
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
                if isinstance(parsed, dict) and ("style" in parsed or "issue_type" in parsed or "identification" in parsed or "intent" in parsed or "colors" in parsed):
                    set_cached_response(ack, parsed)
                    return jsonify(parsed)
        except Exception as e:
            app.logger.error(f"Advise error: {e}")
            return jsonify({"error": str(e)}), 500

        return jsonify({"style": "Stijl niet herkend", "description": "Er is iets misgegaan bij het genereren van het advies.", "confidence": "low"})

    # ── DAMAGE MODE OR LEGACY INSPIRATION (single step) ──
    answers = data.get("answers", None)
    base_prompt = INSPIRATION_PROMPT if mode == "inspiration" else SYSTEM_PROMPT

    # Check cache for damage/legacy mode
    dck = cache_key(mode, "single", image_base64, data.get("goal", ""))
    dcached = get_cached_response(dck)
    if dcached:
        return jsonify(dcached)

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
                set_cached_response(dck, parsed)
                return jsonify(parsed)

        return jsonify(random.choice(FALLBACK_ISSUES))

    except Exception as e:
        app.logger.error(f"Analyze error: {e}")
        return jsonify({"error": str(e), "fallback": random.choice(FALLBACK_ISSUES)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
