#!/usr/bin/env python3
"""Fix goBack met exacte indentatie."""
import subprocess

p = "/home/team/shared/backend/templates/index.html"
with open(p, "rb") as f:
    raw = f.read()

# Exact bytes van de huidige goBack functie (regel 846-852)
old = b'''    function goBack() {
  if (currentStep === "diy" || currentStep === "pro") {
    showResults(currentResult);
  } else {
    goHome();
  }
}
async function analyze()'''

new = b'''    function goBack() {
  if (currentStep === "diy" || currentStep === "pro") {
    showResults(currentResult);
  } else if (_damageSectionOpen) {
    toggleDamageSection(_damageSectionOpen);
  } else if (_costSectionOpen) {
    toggleCostSection(_costSectionOpen);
  } else if (_repairSectionOpen) {
    toggleRepairSection(_repairSectionOpen);
  } else {
    goHome();
  }
}
async function analyze()'''

if old in raw:
    raw = raw.replace(old, new)
    print("goBack fixed exact match")
else:
    # Try with 4-space body
    old2 = b'''    function goBack() {
    if (currentStep === "diy" || currentStep === "pro") {
      showResults(currentResult);
    } else {
      goHome();
    }
  }
async function analyze()'''
    if old2 in raw:
        raw = raw.replace(old2, new)
        print("goBack fixed 4-space match")
    else:
        print("ERROR: goBack not found with any pattern")
        # Debug: show what's around the area
        idx = raw.find(b'function goBack')
        if idx > 0:
            print(f"Found at byte {idx}: {raw[idx:idx+120]}")
        exit(1)

with open(p, "wb") as f:
    f.write(raw)

r = subprocess.run(["node", "-e", "const fs=require('fs');const s=fs.readFileSync('/home/team/shared/backend/templates/index.html','utf8');const m=s.match(/<script>([\\s\\S]*?)<\\/script>/);try{new Function(m[1]);console.log('JS_OK')}catch(e){console.log('Error: '+e.message)}"], capture_output=True, text=True)
print(r.stdout.strip())