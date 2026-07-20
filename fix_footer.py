#!/usr/bin/env python3
"""Fix: remove duplicate NIEUWE SCAN button, goBack already correct."""
import subprocess

p = "/home/team/shared/backend/templates/index.html"
with open(p, "rb") as f:
    raw = f.read()

# Remove NIEUWE SCAN button (both onclick goHome, duplicate)
old = b'          <div class="footer-btn-grid">\n            <button class="footer-btn-secondary" onclick="goHome()">NIEUWE SCAN</button>\n            <button class="footer-btn-secondary" onclick="goHome()">HOME</button>\n          </div>'
new = b'          <div class="footer-btn-grid">\n            <button class="footer-btn-secondary" onclick="goHome()">HOME</button>\n          </div>'
if old in raw:
    raw = raw.replace(old, new)
    print("Removed duplicate NIEUWE SCAN button")
else:
    print("WARNING: pattern not found, trying alternative")
    # Try with different whitespace
    old2 = b'<button class="footer-btn-secondary" onclick="goHome()">NIEUWE SCAN</button>'
    raw = raw.replace(old2, b'')
    print("Removed NIEUWE SCAN (alternative)")

with open(p, "wb") as f:
    f.write(raw)

# JS check
r = subprocess.run(["node", "-e", "const fs=require('fs');const s=fs.readFileSync('/home/team/shared/backend/templates/index.html','utf8');const m=s.match(/<script>([\\s\\S]*?)<\\/script>/);try{new Function(m[1]);console.log('JS_OK')}catch(e){console.log('Error: '+e.message)}"], capture_output=True, text=True)
print(r.stdout.strip())