#!/usr/bin/env python3
"""Fix goBack: check for open toggle sections first, then goHome."""
import subprocess

p = "/home/team/shared/backend/templates/index.html"
with open(p, "rb") as f:
    raw = f.read()

old = b'''    function goBack() {
      if (currentStep === "diy" || currentStep === "pro") {
        showResults(currentResult);
      } else {
        goHome();
      }
    }'''

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
    }'''

if old in raw:
    raw = raw.replace(old, new)
    print("goBack updated with toggle checks")
else:
    print("WARNING: old pattern not found, trying indentation variant")
    # Try with tabs
    old2 = b'''\tfunction goBack() {
\t  if (currentStep === "diy" || currentStep === "pro") {
\t    showResults(currentResult);
\t  } else {
\t    goHome();
\t  }
\t}'''
    raw = raw.replace(old2, new)
    print("goBack updated (alt)")

with open(p, "wb") as f:
    f.write(raw)

r = subprocess.run(["node", "-e", "const fs=require('fs');const s=fs.readFileSync('/home/team/shared/backend/templates/index.html','utf8');const m=s.match(/<script>([\\s\\S]*?)<\\/script>/);try{new Function(m[1]);console.log('JS_OK')}catch(e){console.log('Error: '+e.message)}"], capture_output=True, text=True)
print(r.stdout.strip())