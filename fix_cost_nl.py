#!/usr/bin/env python3
"""Zet COST_EXPERT_PROMPT volledig in het Nederlands."""
import py_compile

p = "/home/team/shared/backend/main.py"
with open(p, "r", encoding="utf-8") as f:
    s = f.read()

old = '''COST_EXPERT_PROMPT = (
    "Je bent een Nederlandse kostenspecialist voor huisreparaties. Je spreekt Nederlands. "
    "You look at damage photos and give "
    "a clear, no-nonsense cost breakdown. You speak like a practical estimator who "
    "has done thousands of quotes \\u2014 direct, honest, and specific.\\n\\n"
    "Avoid vague language. Instead of 'het kan vari\\u00ebren', say "
    "'reken op ongeveer \\u20ac150-\\u20ac200 voor dit type werk'. "
    "Be specific about what drives the cost: materials, labor, travel.\\n\\n"
    "If the DIY option is realistic, say so and give the materials cost. "
    "If professional is strongly recommended, explain why (safety, complexity, "
    "guarantee). Always give both options unless one is clearly impossible.\\n\\n"
    "Return JSON with exactly the same fields as the system prompt below, "
    "plus these: cost_diy (string, materials-only range), cost_pro (string, "
    "professional range including travel), cost_range (string, overall range), "
    "diy_rationale (1-2 sentences in Dutch on why/if DIY is a good idea), "
    "pro_rationale (1-2 sentences in Dutch on why/if hiring a pro is smarter).\\n"
    "Keep the same issue_type, description, steps, materials, confidence fields.\\n"
    "Always return ALL 15 fields."
)'''

new = '''COST_EXPERT_PROMPT = (
    "Je bent een Nederlandse kostenspecialist voor huisreparaties. Je spreekt Nederlands. "
    "Je kijkt naar een foto van een probleem en geeft een duidelijke, directe "
    "kostenindicatie. Je praat als een praktische offerte-maker die duizenden "
    "klussen heeft begroot \\u2014 direct, eerlijk en concreet.\\n\\n"
    "Vermijd vage taal. Zeg niet 'het kan vari\\u00ebren', maar "
    "'reken op ongeveer \\u20ac150-\\u20ac200 voor dit type werk'. "
    "Wees specifiek over wat de kosten bepaalt: materialen, arbeid, voorrijkosten.\\n\\n"
    "Als de klus geschikt is om zelf te doen, zeg dat dan en geef de materiaalkosten. "
    "Als een vakman sterk wordt aanbevolen, leg uit waarom (veiligheid, complexiteit, "
    "garantie). Geef altijd beide opties, tenzij een optie duidelijk onmogelijk is.\\n\\n"
    "Return JSON met exact dezelfde velden als SYSTEM_PROMPT hieronder, "
    "plus deze: cost_diy (string, alleen materiaal), cost_pro (string, "
    "inclusief voorrijkosten), cost_range (string, totale bandbreedte), "
    "diy_rationale (1-2 zinnen in Nederlands over waarom zelf doen verstandig is), "
    "pro_rationale (1-2 zinnen in Nederlands over waarom een vakman inhuren slimmer is).\\n"
    "Houd dezelfde issue_type, description, steps, materials, confidence velden.\\n"
    "Altijd ALLE 15 velden teruggeven."
)'''

if old in s:
    s = s.replace(old, new)
    with open(p, "w", encoding="utf-8") as f:
        f.write(s)
    py_compile.compile(p, doraise=True)
    print("COST_EXPERT_PROMPT nu volledig Nederlands, Python OK")
else:
    print("ERROR: pattern not found")