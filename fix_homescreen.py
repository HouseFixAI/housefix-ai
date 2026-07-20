#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verwijder neutrale carousel, standaard Klus Hulp met experts."""
import subprocess

p = "/home/team/shared/backend/templates/index.html"
with open(p, "r", encoding="utf-8") as f:
    content = f.read()

# Use actual emoji characters
EMOJI_MAG = '\U0001F50D'   # 🔍
EMOJI_COIN = '\U0001F4B0'  # 💰
EMOJI_WRENCH = '\U0001F6E0\ufe0f'  # 🛠️

# ── 1. Vervang hcCards neutral ──
old = content.find('neutral: [')
if old < 0:
    print("ERROR: neutral array not found")
    exit(1)
end = content.find('],', old)
if end < 0:
    print("ERROR: neutral array end not found")
    exit(1)

# Find the original neutral block (from 'neutral: [' to the next key 'damage: [')
damage_start = content.find('damage: [', end)
if damage_start < 0:
    print("ERROR: damage array not found")
    exit(1)

old_block = content[old:damage_start]
new_block = f'''neutral: [
        {{bg:"url(https://images.unsplash.com/photo-1504307651254-35680f356dfd?w=800&h=480&fit=crop&fm=webp&q=85)", t:"{EMOJI_MAG} Schade Expert", a:"openCameraForIntent('damage_expert')"}},
        {{bg:"url(https://images.unsplash.com/photo-1581578731548-c64695cc6952?w=800&h=480&fit=crop&fm=webp&q=85)", t:"{EMOJI_COIN} Kosten Expert", a:"openCameraForIntent('cost_expert')"}},
        {{bg:"url(https://images.unsplash.com/photo-1581539250439-c96689b516dd?w=800&h=480&fit=crop&fm=webp&q=85)", t:"{EMOJI_WRENCH} Reparatie Expert", a:"openCameraForIntent('repair_expert')"}}
      ],
      '''
content = content.replace(old_block, new_block)

# ── 2. Standaard mode naar "damage" bij laden ──
content = content.replace('buildCarousel("neutral");', 'setMode("damage");')

# ── 3. resetMode naar setMode damage ──
old_reset_start = content.find('function resetMode() {')
if old_reset_start > 0:
    old_reset_end = content.find('}', old_reset_start)
    if old_reset_end > 0:
        old_reset_block = content[old_reset_start:old_reset_end+1]
        new_reset_block = '''    function resetMode() {
      setMode("damage");
    }'''
        content = content.replace(old_reset_block, new_reset_block)

with open(p, "w", encoding="utf-8") as f:
    f.write(content)
print("Neutral carousel vervangen door experts, Klus Hulp is standaard")

# JS check
r = subprocess.run(["node", "-e", "const fs=require('fs');const s=fs.readFileSync('/home/team/shared/backend/templates/index.html','utf8');const m=s.match(/<script>([\\s\\S]*?)<\\/script>/);try{new Function(m[1]);console.log('JS_OK')}catch(e){console.log('Error: '+e.message)}"], capture_output=True, text=True)
print(r.stdout.strip())