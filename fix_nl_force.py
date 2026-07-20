#!/usr/bin/env python3
"""Add 'ALLES in het Nederlands' line to COST_EXPERT_PROMPT."""
import py_compile

p = "/home/team/shared/backend/main.py"
with open(p, "r", encoding="utf-8") as f:
    s = f.read()

old = 'garantie). Geef altijd beide opties, tenzij een optie duidelijk onmogelijk is.\\n\\n"'
new = 'garantie). Geef altijd beide opties, tenzij een optie duidelijk onmogelijk is.\\n\\n"\n    "ALLES in het Nederlands. Geen Engels. Ook de inhoud van elk veld \\u2014 "\n    "zoals issue_type, description, steps, materials, cause, risk, urgency, advice \\u2014 "\n    "moet in het Nederlands zijn. Absoluut geen Engels.\\n\\n"'

s = s.replace(old, new)
with open(p, "w", encoding="utf-8") as f:
    f.write(s)

py_compile.compile(p, doraise=True)
print("COST_EXPERT_PROMPT: 'ALLES in het Nederlands' toegevoegd, Python OK")