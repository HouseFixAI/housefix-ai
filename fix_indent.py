#!/usr/bin/env python3
"""Fix function scoping: add 4-space indent to showDamageExpert and showRepairExpert."""
p = "/home/team/shared/backend/templates/index.html"
with open(p, "r") as f:
    s = f.read()

# Replace the closing }} + unindented functions with proper indentation
old = '''  currentStep = "diagnose";
}}
function showDamageExpert(r) {
  currentResult = r;
  const snapEl = document.getElementById("snapshot");
  currentResultImage = snapEl.src || "";
  const saveBtn = document.getElementById("saveBtn");
  const rc = document.getElementById("resultContent");
  let html = "";
  if (r.is_fallback || r.no_damage || r.warning) { showResults(r); return; }
  const it = r.issue_type || "Onbekend";
  const desc = r.description || "";
  const conf = r.confidence || "medium";
  const badgeMap = { high: { c: "badge-high", l: "Hoog" }, medium: { c: "badge-medium", l: "Gemiddeld" }, low: { c: "badge-low", l: "Laag" } };
  const b = badgeMap[conf] || badgeMap.medium;'''

new = '''  currentStep = "diagnose";
  }
  function showDamageExpert(r) {
    currentResult = r;
    const snapEl = document.getElementById("snapshot");
    currentResultImage = snapEl.src || "";
    const saveBtn = document.getElementById("saveBtn");
    const rc = document.getElementById("resultContent");
    let html = "";
    if (r.is_fallback || r.no_damage || r.warning) { showResults(r); return; }
    const it = r.issue_type || "Onbekend";
    const desc = r.description || "";
    const conf = r.confidence || "medium";
    const badgeMap = { high: { c: "badge-high", l: "Hoog" }, medium: { c: "badge-medium", l: "Gemiddeld" }, low: { c: "badge-low", l: "Laag" } };
    const b = badgeMap[conf] || badgeMap.medium;'''

s = s.replace(old, new)

# Now fix the showRepairExpert function too (same issue)
old2 = '''  currentStep = "diagnose";
}
function showRepairExpert(r) {
  currentResult = r;
  const snapEl = document.getElementById("snapshot");
  currentResultImage = snapEl.src || "";
  const saveBtn = document.getElementById("saveBtn");
  const rc = document.getElementById("resultContent");
  let html = "";
  if (r.is_fallback || r.no_damage || r.warning) { showResults(r); return; }
  const it = r.issue_type || "Reparatie";'''

new2 = '''  currentStep = "diagnose";
  }
  function showRepairExpert(r) {
    currentResult = r;
    const snapEl = document.getElementById("snapshot");
    currentResultImage = snapEl.src || "";
    const saveBtn = document.getElementById("saveBtn");
    const rc = document.getElementById("resultContent");
    let html = "";
    if (r.is_fallback || r.no_damage || r.warning) { showResults(r); return; }
    const it = r.issue_type || "Reparatie";'''

s = s.replace(old2, new2)

# Fix the inner }}} - change from }} to } } } with proper indent
# The showDamageExpert ends with:
old_end = '''  currentStep = "diagnose";
}

function showRepairExpert'''
new_end = '''  currentStep = "diagnose";
    }
    function showRepairExpert'''
s = s.replace(old_end, new_end)

# Fix showRepairExpert end - it closes at 2-space indent now, should be 4
old_repair_end = '''  currentStep = "diagnose";
}
function showDiyRoute'''
new_repair_end = '''  currentStep = "diagnose";
    }
    function showDiyRoute'''
s = s.replace(old_repair_end, new_repair_end)

with open(p, "w") as f:
    f.write(s)
print("done")