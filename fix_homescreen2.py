#!/usr/bin/env python3
"""Replace neutral carousel with experts, default to damage mode."""
import re, subprocess

p = "/home/team/shared/backend/templates/index.html"
with open(p, "rb") as f:
    raw = f.read()

# Find the neutral array and replace with experts (no surrogates, just text)
# The neutral array ends right before "damage: ["
damage_marker = b'      damage: ['
neutral_text = raw[raw.find(b'neutral: ['):raw.find(damage_marker)]

# Build replacement using only ASCII-safe escapes for emoji
# JavaScript handles the escaping at runtime
replacement = b'''neutral: [
        {bg:"url(https://images.unsplash.com/photo-1504307651254-35680f356dfd?w=800&h=480&fit=crop&fm=webp&q=85)", t:"\\ud83d\\udd0d Schade Expert", a:"openCameraForIntent('damage_expert')"},
        {bg:"url(https://images.unsplash.com/photo-1581578731548-c64695cc6952?w=800&h=480&fit=crop&fm=webp&q=85)", t:"\\ud83d\\udcb0 Kosten Expert", a:"openCameraForIntent('cost_expert')"},
        {bg:"url(https://images.unsplash.com/photo-1581539250439-c96689b516dd?w=800&h=480&fit=crop&fm=webp&q=85)", t:"\\ud83d\\udee0\\ufe0f Reparatie Expert", a:"openCameraForIntent('repair_expert')"}
      ],
      '''

raw = raw.replace(neutral_text, replacement)

# Replace buildCarousel("neutral") with setMode("damage")
raw = raw.replace(b'buildCarousel("neutral");', b'setMode("damage");')

# Replace resetMode
old_reset_start = raw.find(b'function resetMode() {')
old_reset_end = raw.find(b'}', old_reset_start) + 1
old_reset = raw[old_reset_start:old_reset_end]
new_reset = b'''    function resetMode() {
      setMode("damage");
    }'''
raw = raw.replace(old_reset, new_reset)

with open(p, "wb") as f:
    f.write(raw)
print("Done: neutral carousel replaced with experts, default damage mode")

r = subprocess.run(["node", "-e", "const fs=require('fs');const s=fs.readFileSync('/home/team/shared/backend/templates/index.html','utf8');const m=s.match(/<script>([\\s\\S]*?)<\\/script>/);try{new Function(m[1]);console.log('JS_OK')}catch(e){console.log('Error: '+e.message)}"], capture_output=True, text=True)
print(r.stdout.strip())