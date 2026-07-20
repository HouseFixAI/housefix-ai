#!/usr/bin/env python3
"""Fix Kosten Expert toggle: verwijder opacity uit showCostDiy/showCostPro, alleen toggle bepaalt."""
import subprocess

p = "/home/team/shared/backend/templates/index.html"
with open(p, "r") as f:
    s = f.read()

# Remove opacity lines from showCostDiy
old1 = """      dd.innerHTML = html;
      document.getElementById("costDiyBtn").style.opacity = "0.6";
      document.getElementById("costProBtn").style.opacity = "1";
    }

    function showCostPro"""
new1 = """      dd.innerHTML = html;
    }

    function showCostPro"""
s = s.replace(old1, new1)

# Remove opacity lines from showCostPro
old2 = """      dd.innerHTML = html;
      document.getElementById("costProBtn").style.opacity = "0.6";
      document.getElementById("costDiyBtn").style.opacity = "1";
    }"""
new2 = """      dd.innerHTML = html;
    }"""
s = s.replace(old2, new2)

with open(p, "w") as f:
    f.write(s)
print("Opacity verwijderd uit showCostDiy/showCostPro")

# JS check
r = subprocess.run(["node", "-e", """
const fs=require('fs');
const s=fs.readFileSync('/home/team/shared/backend/templates/index.html','utf8');
const m=s.match(/<script>([\\s\\S]*?)<\\/script>/);
try{new Function(m[1]);console.log('JS_OK')}catch(e){console.log('Error: '+e.message)}
"""], capture_output=True, text=True)
print(r.stdout.strip())