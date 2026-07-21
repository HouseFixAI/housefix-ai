#!/usr/bin/env python3
"""Set selectedCarouselIntent on mode change."""
import subprocess

p = "/home/team/shared/backend/templates/index.html"
with open(p, "r", encoding="utf-8") as f:
    s = f.read()

old = 'function setMode(mode) {\n\t      buildCarousel(mode);\n\t      currentMode = mode;'
new = 'function setMode(mode) {\n\t      buildCarousel(mode);\n\t      currentMode = mode;\n\t      selectedCarouselIntent = mode === "damage" ? "damage_expert" : mode === "inspiration" ? "identify" : null;'

if old in s:
    s = s.replace(old, new)
    with open(p, "w", encoding="utf-8") as f:
        f.write(s)
    print("setMode updated")
else:
    print("ERROR: pattern not found")
    # try with spaces
    old2 = 'function setMode(mode) {\n      buildCarousel(mode);\n      currentMode = mode;'
    if old2 in s:
        s = s.replace(old2, old2 + '\n      selectedCarouselIntent = mode === "damage" ? "damage_expert" : mode === "inspiration" ? "identify" : null;')
        with open(p, "w", encoding="utf-8") as f:
            f.write(s)
        print("setMode updated (spaces)")

r = subprocess.run(["node", "-e", "const fs=require('fs');const s=fs.readFileSync('/home/team/shared/backend/templates/index.html','utf8');const m=s.match(/<script>([\\s\\S]*?)<\\/script>/);try{new Function(m[1]);console.log('JS_OK')}catch(e){console.log('Error: '+e.message)}"], capture_output=True, text=True, cwd="/home/team/shared")
print("JS:", r.stdout.strip())