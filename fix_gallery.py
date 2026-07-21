#!/usr/bin/env python3
"""Koppel galerij-knop aan selectedCarouselIntent."""
import subprocess

p = "/home/team/shared/backend/templates/index.html"
with open(p, "r", encoding="utf-8") as f:
    s = f.read()

old = 'function openGalleryPicker() { currentIntent = currentMode ? (currentMode === "damage" ? "identify_issue" : "identify") : null;'
new = 'function openGalleryPicker() { currentIntent = selectedCarouselIntent || (currentMode ? (currentMode === "damage" ? "identify_issue" : "identify") : null);'

if old in s:
    s = s.replace(old, new)
    with open(p, "w", encoding="utf-8") as f:
        f.write(s)
    print("openGalleryPicker fixed")
else:
    print("ERROR: pattern not found")
    # Try alternative
    import re
    idx = s.find("openGalleryPicker")
    if idx > 0:
        print(f"Found at {idx}: {s[idx:idx+120]}")

r = subprocess.run(["node", "-e", "const fs=require('fs');const s=fs.readFileSync('/home/team/shared/backend/templates/index.html','utf8');const m=s.match(/<script>([\\s\\S]*?)<\\/script>/);try{new Function(m[1]);console.log('JS_OK')}catch(e){console.log('Error: '+e.message)}"], capture_output=True, text=True, cwd="/home/team/shared")
print("JS:", r.stdout.strip())