#!/usr/bin/env python3
"""Add cause/risk/urgency/advice fields to SYSTEM_PROMPT JSON keys + fix frontend fallback."""
import subprocess

# ── 1. Backend: add fields ──
p = "/home/team/shared/backend/main.py"
with open(p, "r") as f:
    s = f.read()

old = '''    "confidence (high/medium/low).\\n"
    "Always return ALL 9 fields. Wees precies met kosten. "'''
new = '''    "confidence (high/medium/low),\\n"
    "cause (1-2 sentences in Dutch explaining what likely caused this issue),\\n"
    "risk (1 sentence in Dutch if there is risk of worsening, else empty string),\\n"
    "urgency (one of 'high', 'medium', 'low'),\\n"
    "advice (1-2 sentences in Dutch: what to do now, practical and direct).\\n"
    "Always return ALL 13 fields. Wees precies met kosten. "'''

s = s.replace(old, new)
with open(p, "w") as f:
    f.write(s)
print("Backend: fields added")

# Validate Python
try:
    import py_compile
    py_compile.compile(p, doraise=True)
    print("Python syntax OK")
except Exception as e:
    print(f"Python error: {e}")

# ── 2. Frontend: fix fallback in showDamageDetails and showDamageAdvice ──
p2 = "/home/team/shared/backend/templates/index.html"
with open(p2, "r") as f:
    s2 = f.read()

# Fix showDamageDetails fallback
old_det = '''      if (!r.cause && !r.risk) {
        html += '<div style="font-size:13px;color:var(--text-muted);text-align:center;padding:8px 0">Geen verdere details beschikbaar voor deze schade.</div>';
      }'''
new_det = '''      if (!r.cause && !r.risk) {
        html += '<div style="font-size:13px;color:var(--text-secondary);line-height:1.6">'+ (r.description || "Geen verdere details beschikbaar voor deze schade.") +'</div>';
      }'''
s2 = s2.replace(old_det, new_det)
print(f"showDamageDetails fallback: {s2.count(old_det) > 0}")

# Fix showDamageAdvice fallback
old_adv = '''      if (!r.advice && !r.cause && !r.risk) {
        html += '<div style="font-size:13px;color:var(--text-muted);text-align:center;padding:8px 0">Geen specifiek advies beschikbaar. Gebruik de knoppen hieronder om reparatie-opties te bekijken.</div>';
      }'''
new_adv = '''      if (!r.advice && !r.cause && !r.risk) {
        html += '<div style="font-size:13px;color:var(--text-secondary);line-height:1.6">'+ (r.description || "Geen specifiek advies beschikbaar. Gebruik de knoppen hieronder om reparatie-opties te bekijken.") +'</div>';
      }'''
s2 = s2.replace(old_adv, new_adv)
print(f"showDamageAdvice fallback: {s2.count(old_adv) > 0}")

with open(p2, "w") as f:
    f.write(s2)

# JS check
r = subprocess.run(["node", "-e", """
const fs=require('fs');
const s=fs.readFileSync('backend/templates/index.html','utf8');
const m=s.match(/<script>([\\s\\S]*?)<\\/script>/);
try{new Function(m[1]);console.log('JS_OK')}catch(e){console.log('JS Error: '+e.message)}
"""], capture_output=True, text=True, cwd="/home/team/shared")
print(r.stdout.strip())