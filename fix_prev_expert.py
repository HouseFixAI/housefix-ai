#!/usr/bin/env python3
"""Add _previousExpert and navigateTo for back navigation."""
import subprocess

p = "/home/team/shared/backend/templates/index.html"
with open(p, "rb") as f:
    raw = f.read()

# 1. Add _previousExpert variable
raw = raw.replace(b'var _repairSectionOpen = null;', b'var _repairSectionOpen = null;\n    var _previousExpert = null;')

# 2. Replace onclick in Schade Expert's Repareren and Kosten buttons
# Use a navigateTo wrapper function instead of inline JS
old_rep = b'<button class="cta-btn" onclick="showRepairExpert(currentResult)" style="padding:12px;font-size:13px;font-weight:600;background:transparent;color:var(--text-primary);border:1.5px solid var(--border-light)">'
new_rep = b'<button class="cta-btn" onclick="_previousExpert=\x27damage\x27; showRepairExpert(currentResult)" style="padding:12px;font-size:13px;font-weight:600;background:transparent;color:var(--text-primary);border:1.5px solid var(--border-light)">'
raw = raw.replace(old_rep, new_rep)

old_cost = b'<button class="cta-btn" onclick="showCostEstimate(currentResult)" style="padding:12px;font-size:13px;font-weight:600;background:transparent;color:var(--text-primary);border:1.5px solid var(--border-light)">'
new_cost = b'<button class="cta-btn" onclick="_previousExpert=\x27damage\x27; showCostEstimate(currentResult)" style="padding:12px;font-size:13px;font-weight:600;background:transparent;color:var(--text-primary);border:1.5px solid var(--border-light)">'
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
  } else if (_previousExpert === 'damage') {
    _previousExpert = null;
    showDamageExpert(currentResult);
  } else {
    goHome();
  }
}'''

raw = raw.replace(old_gb, new_gb)

with open(p, "wb") as f:
    f.write(raw)
print("_previousExpert added, goBack updated")

r = subprocess.run(["node", "-e", "const fs=require('fs');const s=fs.readFileSync('/home/team/shared/backend/templates/index.html','utf8');const m=s.match(/<script>([\\s\\S]*?)<\\/script>/);try{new Function(m[1]);console.log('JS_OK')}catch(e){console.log('Error: '+e.message)}"], capture_output=True, text=True)
print(r.stdout.strip())