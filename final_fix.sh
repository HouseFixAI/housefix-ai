#!/usr/bin/env bash
# Final fix: restart from clean git state, reapply all specialist changes
set -e

cd /home/team/shared

# Restore clean state
git checkout -- backend/templates/index.html

# Run the specialist builders in order
python3 build_specialists.py
python3 specialists_phase2.py

# Fix indentation
python3 -c "
p='backend/templates/index.html'
with open(p,'r') as f: s=f.read()

# Remove duplicate showDamageExpert
idx1=s.find('function showDamageExpert')
idx2=s.find('function showDamageExpert', idx1+10)
if idx2>0:
    prev=s.rfind('}', idx1, idx2)
    if prev>idx1: s=s[:prev]+s[idx2:]

# Fix indentation of showDamageExpert and showRepairExpert
s=s.replace('  currentStep = \"diagnose\";\n}}\nfunction showDamageExpert', '  currentStep = \"diagnose\";\n  }\n  function showDamageExpert')
s=s.replace('  currentStep = \"diagnose\";\n}\nfunction showRepairExpert', '  currentStep = \"diagnose\";\n  }\n  function showRepairExpert')
s=s.replace('    currentStep = \"diagnose\";\n    }\n    function showDiyRoute', '    currentStep = \"diagnose\";\n    }\n    function showDiyRoute')
# Fix showRepairExpert closing too
s=s.replace('  currentStep = \"diagnose\";\n}\nfunction showDiyRoute', '  currentStep = \"diagnose\";\n  }\n  function showDiyRoute')

with open(p,'w') as f: f.write(s)
print('indentation fixed')
"

# Check count of functions
echo "--- Function counts ---"
grep -c "function showDamageExpert\|showRepairExpert" backend/templates/index.html

# Try node check on extracted script
echo "--- JS Syntax check ---"
node -e "
const fs=require('fs');
const s=fs.readFileSync('backend/templates/index.html','utf8');
const m=s.match(/<script>([\s\S]*?)<\/script>/);
try{
    new Function(m[1]);
    console.log('JS_OK');
}catch(e){
    console.log('Error: '+e.message);
    // Show context
    const lines=m[1].split('\n');
    for(let i=0;i<lines.length;i++){
        if(lines[i].includes('function showDamageExpert')||lines[i].includes('function showRepairExpert')){
            console.log('Line '+(i+703)+': '+lines[i].trim().substring(0,80));
        }
    }
}
"

# Restart server
pkill -f "python3 main.py" 2>/dev/null || true
sleep 0.5
cd backend && python3 main.py > /tmp/backend.log 2>&1 &
sleep 1
curl -s http://localhost:8000/api/health