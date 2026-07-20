#!/usr/bin/env python3
"""Reparatie Expert: eigen AI-stem (klusjesman/vakman, oplossingsgericht)."""
import py_compile

p = "/home/team/shared/backend/main.py"
with open(p, "r") as f:
    s = f.read()

# ── 1. Voeg REPAIR_EXPERT_PROMPT toe na COST_EXPERT_PROMPT ──
repair_prompt = '''
REPAIR_EXPERT_PROMPT = (
    "Je bent een ervaren klusjesman/vakman die al duizenden reparaties heeft gedaan. "
    "Een huiseigenaar stuurt je een foto van een probleem. Jij kijkt ernaar en zegt "
    "direct hoe het op te lossen. Niet de oorzaak, maar de oplossing staat centraal.\\n\\n"
    "Spreek in korte, duidelijke zinnen. Gebruik normaal Nederlands, geen "
    "bureaucratische taal. Zeg niet 'het wordt geadviseerd om', maar "
    "'dit doe je zo:'.\\n\\n"
    "Geef altijd een tijdsindicatie (\\u2018reken op 2 uurtjes\\u2019, \\u2018ben je in 30 minuten klaar\\u2019) "
    "en een moeilijkheidsgraad (makkelijk/medium/moeilijk). Wees eerlijk: als het "
    "ingewikkeld is, zeg het dan. Een vakman inschakelen is soms slimmer.\\n\\n"
    "Waarschuw voor veelgemaakte fouten: \\u2018Let op: niet te veel water in het mengsel, "
    "anders blijft het plakken\\u2019.\\n\\n"
    "Return JSON met exact dezelfde velden als SYSTEM_PROMPT hieronder, plus:\\n"
    "estimate_time (string in Dutch, e.g. \\u2018\\u00b1 2 uur\\u2019, \\u201830 minuten\\u2019),\\n"
    "difficulty (string in Dutch: \\u2018Makkelijk\\u2019, \\u2018Gemiddeld\\u2019, \\u2018Moeilijk\\u2019),\\n"
    "diy_rationale (1 zin in Dutch: waarom dit goed zelf te doen is),\\n"
    "pro_rationale (1 zin in Dutch: waarom een vakman beter is).\\n"
    "Houd dezelfde issue_type, description, steps, materials, cost_diy, cost_pro, "
    "confidence, cause, risk, urgency, advice velden. Altijd ALLE velden teruggeven."
)
'''

# Find the end of COST_EXPERT_PROMPT (the closing ")" after COST_EXPERT_PROMPT)
# Look for the pattern after "Return ALL 15 fields." 
marker = 'Return ALL 15 fields.'
idx_marker = s.find(marker)
if idx_marker > 0:
    # Find the closing parenthesis after this marker (end of COST_EXPERT_PROMPT)
    end_quote = s.find('"', idx_marker)  # Find the closing " of the last line
    if end_quote > 0:
        close_paren = s.find(')', end_quote)
        if close_paren > 0:
            # Insert after the )
            s = s[:close_paren+1] + "\n" + repair_prompt + s[close_paren+1:]
            print("REPAIR_EXPERT_PROMPT added")
        else:
            print("ERROR: closing paren not found")
    else:
        print("ERROR: closing quote not found")
else:
    print("ERROR: marker not found, trying alternative")
    # Try inserting right before REPAIR_EXPERT_PROMPT will be defined
    # Find the end of SYSTEM_PROMPT
    idx_system_end = s.find("\n# ── Session Cache")
    if idx_system_end > 0:
        s = s[:idx_system_end] + "\n" + repair_prompt + "\n" + s[idx_system_end:]
        print("REPAIR_EXPERT_PROMPT added (alternative position)")

# ── 2. Koppel repair_expert intent aan REPAIR_EXPERT_PROMPT ──
old_logic = """    if mode == "damage" and user_intent_analyze == "cost_expert":
        base_prompt = COST_EXPERT_PROMPT
    elif mode == "damage" and user_intent_analyze == "repair_expert":
        base_prompt = SYSTEM_PROMPT"""

new_logic = """    if mode == "damage" and user_intent_analyze == "cost_expert":
        base_prompt = COST_EXPERT_PROMPT
    elif mode == "damage" and user_intent_analyze == "repair_expert":
        base_prompt = REPAIR_EXPERT_PROMPT"""

s = s.replace(old_logic, new_logic)

with open(p, "w") as f:
    f.write(s)
print("Repair expert intent gekoppeld aan REPAIR_EXPERT_PROMPT")

# Python syntax check
py_compile.compile(p, doraise=True)
print("Python syntax OK")