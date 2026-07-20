#!/usr/bin/env python3
"""Use navigateTo function instead of inline _previousExpert set."""
import subprocess

p = "/home/team/shared/backend/templates/index.html"
with open(p, "rb") as f:
    raw = f.read()

# 1. Add _previousExpert + navigateTo function
old_var = b'    var _previousExpert = null;'
new_var = b'''    var _previousExpert = null;
    function navigateTo(expert) {
      _previousExpert = 'damage';
      if (expert === 'repair') showRepairExpert(currentResult);
      else if (expert === 'cost') showCostEstimate(currentResult);
    }'''
raw = raw.replace(old_var, new_var)

# 2. Replace onclick in Schade Expert's buttons
old_rep = b'onclick="_previousExpert=\\x27damage\\x27; showRepairExpert(currentResult)"'
new_rep = b'onclick="navigateTo(\'repair\')"'
raw = raw.replace(old_rep, new_rep)

old_cost = b'onclick="_previousExpert=\\x27damage\\x27; showCostEstimate(currentResult)"'
new_cost = b'onclick="navigateTo(\'cost\')"'
raw = raw.replace(old_cost, new_cost)

with open(p, "wb") as f:
    f.write(raw)
print("navigateTo added")

r = subprocess.run(["node", "-e", "const fs=require('fs');const s=fs.readFileSync('/home/team/shared/backend/templates/index.html','utf8');const m=s.match(/<script>([\\s\\S]*?)<\\/script>/);try{new Function(m[1]);console.log('JS_OK')}catch(e){console.log('Error: '+e.message)}"], capture_output=True, text=True, cwd="/home/team/shared")
print(r.stdout.strip())