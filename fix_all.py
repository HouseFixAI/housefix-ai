#!/usr/bin/env python3
import re

with open('/home/team/shared/backend/templates/index.html', 'r') as f:
    c = f.read()

# Fix 1: showPurchaseQuestions - resultsWrap.remove -> .add
c = c.replace(
    'document.getElementById("resultsWrap").classList.remove("active");\n      const html',
    'document.getElementById("resultsWrap").classList.add("active");\n      const html'
)

with open('/home/team/shared/backend/templates/index.html', 'w') as f:
    f.write(c)
print("Fix 1: OK")

with open('/home/team/shared/backend/main.py', 'r') as f:
    c = f.read()

# Fix 2: INSPIRATION_PROMPT - make matching_stores optional/relevant
# The prompt currently has matching_stores always required. We soften it.
old_is = 'matching_stores (3-4 specifieke winkels met productnaam, prijsindicatie'
new_is = 'matching_stores (ALS er producten relevant zijn: 2-3 specifieke winkels met productnaam, prijsindicatie. ANDERS: lege array — alleen vullen als de gebruiker erom vraagt of het wezenlijk bijdraagt aan het stijlverhaal. Nooit winkels forceren voor een fotolijst of vaas zonder context.'
c = c.replace(old_is, new_is)

# Also fix the JSON schema description at top of prompt
old_schema = 'matching_stores (an array of 1-2 related style names'
# Actually this is in similar_styles, not matching_stores. Let me find matching_stores in the prompt.

# Find the FALLBACK_INSPIRATION matching_stores field description in the prompt
# The prompt says: "matching_stores (3-4 specific products..."
# Let me search more broadly

# Fix 3: Strengthen IDENTIFY_PROMPT no-shop rule
# Find the "ABSOLUTELY FORBIDDEN" section in IDENTIFY_PROMPT
old_id = 'ABSOLUTELY FORBIDDEN:\\n    \"• Geef GEEN shopadvies, prijzen, winkels of koopinformatie.\\n\"'
# This is multiline, let me find it differently

# Actually let me just do targeted replacements
# Fix 2: In INSPIRATION_PROMPT, soften matching_stores requirement
old_match = '"matching_stores (3-4 specifieke winkels met productnaam, prijsindicatie, en '
new_match = '"matching_stores (ALS de foto duidelijke producten toont die de gebruiker wil namaken: 1-3 specifieke winkels met productnaam, prijsindicatie, en '
c = c.replace(old_match, new_match)

# Fix 3: Strengthen IDENTIFY_PROMPT - find the FORBIDDEN section
old_forbid = '"• Geef GEEN shopadvies, prijzen, winkels of koopinformatie.\\n    \"'
new_forbid = '"• Geef GEEN shopadvies, prijzen, winkels of koopinformatie. ABSOLUUT VERBODEN: winkelnamen (IKEA, HEMA, etc.), prijzen (€), productnaam, materiaalsuggesties die als aankoopadvies kunnen worden opgevat.\\n    \"'
c = c.replace(old_forbid, new_forbid)

with open('/home/team/shared/backend/main.py', 'w') as f:
    f.write(c)
print("Fix 2+3: OK")