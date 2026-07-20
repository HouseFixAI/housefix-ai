#!/usr/bin/env python3
"""Herstel Interieur: carousel, switch, navigatie. Hulp blijft intact."""
p = "/home/team/shared/backend/templates/index.html"
with open(p, "r") as f:
    s = f.read()

# ── 1. Herstel inspiration carousel naar origineel ──
old_inspo = """      inspiration: [
        {bg:"url(https://images.unsplash.com/photo-1513519245088-0e12902e35ca?w=800&h=480&fit=crop&fm=webp&q=85)", t:"\\ud83c\\udfe1 Wooncoach", a:"openCameraForIntent('interior_coach')"},
        {bg:"url(https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=800&h=480&fit=crop&fm=webp&q=85)", t:"\\ud83d\\udccb Shopadvies", a:"openCameraForIntent('identify')"},
        {bg:"url(https://images.unsplash.com/photo-1616486338812-3dadae4b4ace?w=800&h=480&fit=crop&fm=webp&q=85)", t:"Stijl mijn Kamer", a:"openCameraForIntent('style_room')"},
        {bg:"url(https://images.unsplash.com/photo-1513694203232-719a280e022f?w=800&h=480&fit=crop&fm=webp&q=85)", t:"Raamdecoratie", a:"openCamera()"}
      ]"""
new_inspo = """      inspiration: [
        {bg:"url(https://images.unsplash.com/photo-1513519245088-0e12902e35ca?w=800&h=480&fit=crop&fm=webp&q=85)", t:"Scan voor Kleurenpalet", a:"openCameraForIntent('identify')"},
        {bg:"url(https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=800&h=480&fit=crop&fm=webp&q=85)", t:"Vind dit Meubel", a:"openCameraForIntent('find_item')"},
        {bg:"url(https://images.unsplash.com/photo-1616486338812-3dadae4b4ace?w=800&h=480&fit=crop&fm=webp&q=85)", t:"Stijl mijn Kamer", a:"openCameraForIntent('style_room')"},
        {bg:"url(https://images.unsplash.com/photo-1513694203232-719a280e022f?w=800&h=480&fit=crop&fm=webp&q=85)", t:"Raamdecoratie", a:"openCamera()"}
      ]"""
s = s.replace(old_inspo, new_inspo)

# ── 2. Verwijder interior_coach case uit switch ──
old_switch = """          case "interior_coach":
            showInteriorCoach(data);
            break;"""
s = s.replace(old_switch, "")

# ── 3. Voeg case "cost" terug voor backward compat ──
# Het moet na cost_expert komen, zodat cost_expert vóór cost wordt gematched
# Zoek huidige cost_expert case
cost_block = """          case "cost_expert":
            showCostEstimate(data);
            break;"""
# We willen cost_expert houden, en cost toevoegen als fallback
# Voeg case "cost" toe ná cost_expert
cost_fallback = """
          case "cost":
            showCostEstimate(data);
            break;"""
s = s.replace(cost_block, cost_block + cost_fallback)

# ── 4. Check of showCostEstimate functie bestaat ──
if "function showCostEstimate" in s:
    print("showCostEstimate function exists")
else:
    print("WARNING: showCostEstimate function missing")

with open(p, "w") as f:
    f.write(s)
print("Restore complete")

# ── 5. JS syntax check ──
import subprocess
r = subprocess.run(["node", "-e", """
const fs=require('fs');
const s=fs.readFileSync('backend/templates/index.html','utf8');
const m=s.match(/<script>([\\s\\S]*?)<\\/script>/);
try{new Function(m[1]);console.log('JS_OK')}catch(e){console.log('JS Error: '+e.message)}
"""], capture_output=True, text=True, cwd="/home/team/shared")
print(r.stdout.strip())
if r.stderr:
    print(r.stderr.strip())