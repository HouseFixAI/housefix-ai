#!/usr/bin/env python3
"""Fresh fix: restore index.html, apply navigateTo properly."""
import subprocess, os

os.chdir("/home/team/shared")

# Restore clean file
subprocess.run(["git", "restore", "backend/templates/index.html"], check=True)

p = "backend/templates/index.html"
with open(p, "rb") as f:
    raw = f.read()

# 1. Add _previousExpert variable
raw = raw.replace(b'var _repairSectionOpen = null;', b'var _repairSectionOpen = null;\n    var _previousExpert = null;\n    function navigateTo(e) {\n      _previousExpert = "damage";\n      if (e === "repair") showRepairExpert(currentResult);\n      else if (e === "cost") showCostEstimate(currentResult);\n    }')

# 2. Replace onclick in Schade buttons - search for the buttons without _previousExpert
# Repareren button
old_rep = b'onclick="showRepairExpert(currentResult)" style="padding:12px;font-size:13px;font-weight:600;background:transparent;color:var(--text-primary);border:1.5px solid var(--border-light)">'
new_rep = b'onclick="navigateTo(\'repair\')" style="padding:12px;font-size:13px;font-weight:600;background:transparent;color:var(--text-primary);border:1.5px solid var(--border-light)">'
raw = raw.replace(old_rep, new_rep)

# Kosten button  
old_cost = b'onclick="showCostEstimate(currentResult)" style="padding:12px;font-size:13px;font-weight:600;background:transparent;color:var(--text-primary);border:1.5px solid var(--border-light)">'
new_cost = b'onclick="navigateTo(\'cost\')" style="padding:12px;font-size:13px;font-weight:600;background:transparent;color:var(--text-primary);border:1.5px solid var(--border-light)">'
raw = raw.replace(old_cost, new_cost)

# 3. Update goBack
old_gb = b'''    function goBack() {
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

new_gb = b'''    function goBack() {
  if (currentStep === "diy" || currentStep === "pro") {
    showResults(currentResult);
  } else if (_damageSectionOpen) {
    toggleDamageSection(_damageSectionOpen);
  } else if (_costSectionOpen) {
    toggleCostSection(_costSectionOpen);
  } else if (_repairSectionOpen) {
    toggleRepairSection(_repairSectionOpen);
  } else if (_previousExpert === "damage") {
    _previousExpert = null;
    showDamageExpert(currentResult);
  } else {
    goHome();
  }
}'''

raw = raw.replace(old_gb, new_gb)

with open(p, "wb") as f:
    f.write(raw)
print("All fixes applied from clean state")

r = subprocess.run(["node", "-e", "const fs=require('fs');const s=fs.readFileSync('backend/templates/index.html','utf8');const m=s.match(/<script>([\\s\\S]*?)<\\/script>/);try{new Function(m[1]);console.log('JS_OK')}catch(e){console.log('Error: '+e.message)}"], capture_output=True, text=True, cwd="/home/team/shared")
print("JS:", r.stdout.strip())
if r.stderr.strip():
    print("STDERR:", r.stderr.strip())