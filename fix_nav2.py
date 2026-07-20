#!/usr/bin/env python3
"""Fix: navigateTo with simpler syntax."""
import subprocess, os
os.chdir("/home/team/shared")
subprocess.run(["git", "restore", "backend/templates/index.html"])

p = "backend/templates/index.html"
with open(p, "rb") as f:
    raw = f.read()

# 1. Add _previousExpert + navigateTo
raw = raw.replace(b'var _repairSectionOpen = null;', b'var _repairSectionOpen = null;\n    var _previousExpert = null;\n    function goToExpert(t){_previousExpert="damage";if(t==="repair"){showRepairExpert(currentResult)}else if(t==="cost"){showCostEstimate(currentResult)}}')

# 2. Replace onclick
raw = raw.replace(b'onclick="showRepairExpert(currentResult)" style="padding:12px;font-size:13px;font-weight:600;background:transparent;color:var(--text-primary);border:1.5px solid var(--border-light)">', b'onclick="goToExpert(\'repair\')" style="padding:12px;font-size:13px;font-weight:600;background:transparent;color:var(--text-primary);border:1.5px solid var(--border-light)">')
raw = raw.replace(b'onclick="showCostEstimate(currentResult)" style="padding:12px;font-size:13px;font-weight:600;background:transparent;color:var(--text-primary);border:1.5px solid var(--border-light)">', b'onclick="goToExpert(\'cost\')" style="padding:12px;font-size:13px;font-weight:600;background:transparent;color:var(--text-primary);border:1.5px solid var(--border-light)">')

# 3. Update goBack
raw = raw.replace(b'  } else {\n    goHome();\n  }\n}\nasync function analyze()', b'  } else if (_previousExpert === "damage") {\n    _previousExpert = null;\n    showDamageExpert(currentResult);\n  } else {\n    goHome();\n  }\n}\nasync function analyze()')

with open(p, "wb") as f:
    f.write(raw)
print("Done")

r = subprocess.run(["node", "-e", "const fs=require('fs');const s=fs.readFileSync('backend/templates/index.html','utf8');const m=s.match(/<script>([\\s\\S]*?)<\\/script>/);try{new Function(m[1]);console.log('JS_OK')}catch(e){console.log('Error: '+e.message)}"], capture_output=True, text=True, cwd="/home/team/shared")
print("JS:", r.stdout.strip())