#!/usr/bin/env python3
"""Kosten Expert: eigen AI-stem (zakelijk, direct, offerte-achtig)."""
import subprocess

p = "/home/team/shared/backend/main.py"
with open(p, "r") as f:
    s = f.read()

# ── 1. Voeg COST_EXPERT_PROMPT toe na SYSTEM_PROMPT ──
cost_prompt = '''
COST_EXPERT_PROMPT = (
    "You are a Dutch home repair cost specialist. You look at damage photos and give "
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
)
'''

# Insert after SYSTEM_PROMPT definition (after the closing parenthesis)
old_marker = 'Always return ALL 13 fields. Wees precies met kosten. "'
new_marker = 'Always return ALL 13 fields. Wees precies met kosten. "'
idx = s.find(old_marker)
if idx > 0:
    # Find the closing ")" of SYSTEM_PROMPT
    end_idx = s.find(")", idx)
    if end_idx > 0:
        # Insert cost prompt after SYSTEM_PROMPT closes
        insert_at = end_idx + 1
        s = s[:insert_at] + "\n" + cost_prompt + s[insert_at:]
        print("COST_EXPERT_PROMPT added")
    else:
        print("ERROR: SYSTEM_PROMPT closing paren not found")
else:
    print("ERROR: SYSTEM_PROMPT marker not found")

# ── 2. Pas damage mode logica aan: gebruik COST_EXPERT_PROMPT voor cost_expert intent ──
old_damage = """    # ── DAMAGE MODE OR LEGACY INSPIRATION (single step) ──
    answers = data.get("answers", None)
    base_prompt = INSPIRATION_PROMPT if mode == "inspiration" else SYSTEM_PROMPT"""

new_damage = """    # ── DAMAGE MODE OR LEGACY INSPIRATION (single step) ──
    answers = data.get("answers", None)
    # Select expert prompt based on user_intent
    user_intent_analyze = data.get("user_intent", "")
    if mode == "damage" and user_intent_analyze == "cost_expert":
        base_prompt = COST_EXPERT_PROMPT
    elif mode == "damage" and user_intent_analyze == "repair_expert":
        base_prompt = SYSTEM_PROMPT
    else:
        base_prompt = INSPIRATION_PROMPT if mode == "inspiration" else SYSTEM_PROMPT"""

s = s.replace(old_damage, new_damage)

with open(p, "w") as f:
    f.write(s)
print("Damage mode logica aangepast: cost_expert gebruikt eigen prompt")

# Python syntax check
try:
    import py_compile
    py_compile.compile(p, doraise=True)
    print("Python syntax OK")
except Exception as e:
    print(f"Python error: {e}")