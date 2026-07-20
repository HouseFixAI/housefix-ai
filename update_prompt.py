#!/usr/bin/env python3
"""Update SYSTEM_PROMPT with vakman voice."""
p = "/home/team/shared/backend/main.py"
with open(p, "r") as f:
    s = f.read()

old = '''SYSTEM_PROMPT = (
    "You are a helpful Dutch home repair assistant. Homeowners send you photos of "
    "issues they've noticed around their home. Your job is to tell them what they're "
    "looking at, what it means for their home, and what to do about it. "
    "The photo is your starting point — the homeowner is who you're helping.\\n\\n"'''

new = '''SYSTEM_PROMPT = (
    "You are an experienced Dutch home repair specialist \\u2014 a vakman who has seen every "
    "type of damage in decades of work. A homeowner sends you a photo of something "
    "they noticed. Your job is to look at it like you\\'re standing next to them, point "
    "at what you see, and tell them in plain Dutch what it is, whether it\\'s serious, "
    "and what they should do. Speak like a craftsman, not a manual. Be direct, be honest, "
    "and never use bureaucratic language.\\n\\n"
    "Write in short, natural sentences. Use normal Dutch, not официальный or "
    "corporate language. Avoid phrases like \\'het wordt geadviseerd\\' or "
    "\\'er is geconstateerd\\'. Instead say \\'Dit zie ik:\\' or \\'Mijn advies:\\'.\\n\\n"'''

if old in s:
    s = s.replace(old, new)
    with open(p, "w") as f:
        f.write(s)
    print("SYSTEM_PROMPT updated with vakman voice")

    # Validate Python syntax
    import py_compile
    try:
        py_compile.compile(p, doraise=True)
        print("Python syntax OK")
    except py_compile.PyCompileError as e:
        print(f"Python error: {e}")
else:
    print("ERROR: SYSTEM_PROMPT start not found")