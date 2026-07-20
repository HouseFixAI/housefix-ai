#!/usr/bin/env python3
"""Fix COST_EXPERT_PROMPT: add Dutch language instruction."""
p = "/home/team/shared/backend/main.py"
with open(p, "r") as f:
    s = f.read()

old = '''COST_EXPERT_PROMPT = (
    "You are a Dutch home repair cost specialist. You look at damage photos and give '''
new = '''COST_EXPERT_PROMPT = (
    "Je bent een Nederlandse kostenspecialist voor huisreparaties. Je spreekt Nederlands. "
    "You look at damage photos and give '''

s = s.replace(old, new)

with open(p, "w") as f:
    f.write(s)
print("COST_EXPERT_PROMPT: Dutch language instruction added")

import py_compile
py_compile.compile(p, doraise=True)
print("Python syntax OK")