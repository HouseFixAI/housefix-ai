#!/usr/bin/env python3
"""Fix: use wrapper functions instead of inline string parameters."""
import subprocess, os
os.chdir("/home/team/shared")
subprocess.run(["git", "restore", "backend/templates/index.html"])

with open("backend/templates/index.html", "r", encoding="utf-8") as f:
    full = f.read()

# Add _previousExpert + goTo functions after _repairSectionOpen
full = full.replace(
    "var _repairSectionOpen = null;",
    "var _repairSectionOpen = null;\n    var _previousExpert = null;\n    function goToRepair(){_previousExpert='damage';showRepairExpert(currentResult)}\n    function goToCost(){_previousExpert='damage';showCostEstimate(currentResult)}"
)

# Replace onclick for Repareren button
full = full.replace(
    'onclick="showRepairExpert(currentResult)"',
    'onclick="goToRepair()"'
)

# Replace onclick for Kosten button  
full = full.replace(
    'onclick="showCostEstimate(currentResult)"',
    'onclick="goToCost()"'
)

# Update goBack
old_gb = '  } else if (_repairSectionOpen) {\n    toggleRepairSection(_repairSectionOpen);\n  } else {\n    goHome();\n  }\n}\nasync function analyze()'
new_gb = '  } else if (_repairSectionOpen) {\n    toggleRepairSection(_repairSectionOpen);\n  } else if (_previousExpert === "damage") {\n    _previousExpert = null;\n    showDamageExpert(currentResult);\n  } else {\n    goHome();\n  }\n}\nasync function analyze()'

if old_gb in full:
    full = full.replace(old_gb, new_gb)
    print("goBack updated")
else:
    print("WARNING: goBack pattern not found")

with open("backend/templates/index.html", "w", encoding="utf-8") as f:
    f.write(full)
print("Written")

r = subprocess.run(["node", "-e", "const fs=require('fs');const s=fs.readFileSync('backend/templates/index.html','utf8');const m=s.match(/<script>([\\s\\S]*?)<\\/script>/);try{new Function(m[1]);console.log('JS_OK')}catch(e){console.log('Error: '+e.message)}"], capture_output=True, text=True)
print("JS:", r.stdout.strip())