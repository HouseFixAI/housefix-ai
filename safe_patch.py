#!/usr/bin/env python3
"""Safe patch: add _previousExpert + goToExpert + goBack update."""
import subprocess, os
os.chdir("/home/team/shared")

# Start fresh
subprocess.run(["git", "restore", "backend/templates/index.html"], check=True)

with open("backend/templates/index.html", "r", encoding="utf-8") as f:
    lines = f.readlines()

# Find and modify specific lines
new_lines = []
for i, line in enumerate(lines):
    # Add _previousExpert + goToExpert after _repairSectionOpen line
    if "var _repairSectionOpen = null;" in line:
        new_lines.append(line)
        new_lines.append("    var _previousExpert = null;\n")
        new_lines.append("    function goToExpert(t){_previousExpert='damage';if(t==='repair'){showRepairExpert(currentResult)}else if(t==='cost'){showCostEstimate(currentResult)}}\n")
        continue
    
    # Replace onclick for Repareren button
    if 'onclick="showRepairExpert(currentResult)" style="padding:12px;font-size:13px;font-weight:600;background:transparent;color:var(--text-primary);border:1.5px solid var(--border-light)"' in line:
        line = line.replace(
            'onclick="showRepairExpert(currentResult)"',
            'onclick="goToExpert(\'repair\')"'
        )
        new_lines.append(line)
        continue
    
    # Replace onclick for Kosten button
    if 'onclick="showCostEstimate(currentResult)" style="padding:12px;font-size:13px;font-weight:600;background:transparent;color:var(--text-primary);border:1.5px solid var(--border-light)"' in line:
        line = line.replace(
            'onclick="showCostEstimate(currentResult)"',
            'onclick="goToExpert(\'cost\')"'
        )
        new_lines.append(line)
        continue
    
    # Update goBack: add _previousExpert check before else { goHome }
    if '  } else {\n    goHome();\n  }' in line and i > 800:
        # This might be the closing of goBack - replace
        pass
    
    new_lines.append(line)

# For goBack, use string replace on the full text instead
full = "".join(new_lines)

# Replace the specific goBack else clause
old_gb_else = '  } else {\n    goHome();\n  }\n}\nasync function analyze()'
new_gb_else = '  } else if (_previousExpert === "damage") {\n    _previousExpert = null;\n    showDamageExpert(currentResult);\n  } else {\n    goHome();\n  }\n}\nasync function analyze()'

if old_gb_else in full:
    full = full.replace(old_gb_else, new_gb_else)
    print("goBack updated")
else:
    print("WARNING: goBack else clause not found - trying alt")
    # Try with 4-space indent
    old2 = '    } else {\n      goHome();\n    }\n  }\nasync function analyze()'
    new2 = '    } else if (_previousExpert === "damage") {\n      _previousExpert = null;\n      showDamageExpert(currentResult);\n    } else {\n      goHome();\n    }\n  }\nasync function analyze()'
    if old2 in full:
        full = full.replace(old2, new2)
        print("goBack updated (alt)")

with open("backend/templates/index.html", "w", encoding="utf-8") as f:
    f.write(full)
print("Written to file")

r = subprocess.run(["node", "-e", "const fs=require('fs');const s=fs.readFileSync('backend/templates/index.html','utf8');const m=s.match(/<script>([\\s\\S]*?)<\\/script>/);try{new Function(m[1]);console.log('JS_OK')}catch(e){console.log('Error: '+e.message)}"], capture_output=True, text=True)
print("JS:", r.stdout.strip())