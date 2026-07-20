#!/usr/bin/env python3
"""Fix onclick in cost buttons - was nog showCostDiy ipv toggleCostSection."""
import subprocess

p = "/home/team/shared/backend/templates/index.html"
with open(p, "r") as f:
    s = f.read()

# Fix DIY button onclick
old1 = 'onclick="showCostDiy(currentResult)"'
new1 = "onclick=\"toggleCostSection('diy')\""
s = s.replace(old1, new1)

# Fix Pro button onclick
old2 = 'onclick="showCostPro(currentResult)"'
new2 = "onclick=\"toggleCostSection('pro')\""
s = s.replace(old2, new2)

# Also remove -> arrows from buttons if still there
s = s.replace("alleen materiaal \\u2192", "alleen materiaal")
s = s.replace("incl. voorrijkosten \\u2192", "incl. voorrijkosten")
s = s.replace("alleen materiaal →", "alleen materiaal")
s = s.replace("incl. voorrijkosten →", "incl. voorrijkosten")

with open(p, "w") as f:
    f.write(s)

print("onclick fixed")

# JS check
r = subprocess.run(["node", "-e", "const fs=require('fs');const s=fs.readFileSync('/home/team/shared/backend/templates/index.html','utf8');const m=s.match(/<script>([\\s\\S]*?)<\\/script>/);try{new Function(m[1]);console.log('JS_OK')}catch(e){console.log('Error: '+e.message)}"], capture_output=True, text=True)
print(r.stdout.strip())