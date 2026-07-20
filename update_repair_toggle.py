#!/usr/bin/env python3
"""Reparatie Expert: toggle-functionaliteit (klik=toon, nogmaals=weg), geen terug-link."""
import subprocess

p = "/home/team/shared/backend/templates/index.html"
with open(p, "r") as f:
    s = f.read()

# ── 1. showRepairExpert: vervang onclick + verwijder pijltjes ──
old1 = """      html += '<div id="repDiyBtn" onclick="showRepairDiy(currentResult)" style="cursor:pointer;padding:16px;border-radius:var(--radius-sm);background:var(--sage-soft);border:1px solid rgba(138,155,122,0.15);text-align:center;transition:all 0.2s">';"""
new1 = """      html += '<div id="repDiyBtn" onclick="toggleRepairSection(\\'diy\\')" style="cursor:pointer;padding:16px;border-radius:var(--radius-sm);background:var(--sage-soft);border:1px solid rgba(138,155,122,0.15);text-align:center;transition:all 0.2s">';"""
s = s.replace(old1, new1)

old2 = """      html += '<div id="repProBtn" onclick="showRepairPro(currentResult)" style="cursor:pointer;padding:16px;border-radius:var(--radius-sm);background:var(--terracotta-soft);border:1px solid rgba(196,98,74,0.15);text-align:center;transition:all 0.2s">';"""
new2 = """      html += '<div id="repProBtn" onclick="toggleRepairSection(\\'pro\\')" style="cursor:pointer;padding:16px;border-radius:var(--radius-sm);background:var(--terracotta-soft);border:1px solid rgba(196,98,74,0.15);text-align:center;transition:all 0.2s">';"""
s = s.replace(old2, new2)

# Remove "→" from buttons
s = s.replace("Stappenplan \\u2192", "Stappenplan")
s = s.replace("Offerte aanvragen \\u2192", "Offerte aanvragen")
s = s.replace("Stappenplan →", "Stappenplan")
s = s.replace("Offerte aanvragen →", "Offerte aanvragen")

# ── 2. showRepairDiy: verwijder "Andere optie" link ──
old3 = """      html += '<div style="text-align:center;margin-top:8px"><button onclick="showRepairExpert(currentResult)" style="background:none;border:none;color:var(--text-muted);font-size:12px;cursor:pointer;padding:4px 12px">\\u2190 Andere optie</button></div>';
      dd.innerHTML = html;
      document.getElementById("repDiyBtn").style.opacity = "0.6";
      document.getElementById("repProBtn").style.opacity = "1";
    }

    function showRepairPro"""
new3 = """      dd.innerHTML = html;
    }

    function showRepairPro"""
s = s.replace(old3, new3)

# ── 3. showRepairPro: verwijder "Andere optie" link en opacity ──
old4 = """      html += '<div style="text-align:center;margin-top:8px"><button onclick="showRepairExpert(currentResult)" style="background:none;border:none;color:var(--text-muted);font-size:12px;cursor:pointer;padding:4px 12px">\\u2190 Andere optie</button></div>';
      dd.innerHTML = html;
      document.getElementById("repProBtn").style.opacity = "0.6";
      document.getElementById("repDiyBtn").style.opacity = "1";
    }

    function showDiyRoute"""
new4 = """      dd.innerHTML = html;
    }

    function showDiyRoute"""
s = s.replace(old4, new4)

# ── 4. Voeg toggleRepairSection toe vóór showRepairDiy ──
toggle = """
    var _repairSectionOpen = null;
    function toggleRepairSection(section) {
      if (_repairSectionOpen === section) {
        document.getElementById("repDetail").innerHTML = '';
        document.getElementById("repDiyBtn").style.opacity = "1";
        document.getElementById("repProBtn").style.opacity = "1";
        _repairSectionOpen = null;
        return;
      }
      _repairSectionOpen = section;
      if (section === 'diy') {
        document.getElementById("repDiyBtn").style.opacity = "0.6";
        document.getElementById("repProBtn").style.opacity = "1";
        showRepairDiy(currentResult);
      } else {
        document.getElementById("repProBtn").style.opacity = "0.6";
        document.getElementById("repDiyBtn").style.opacity = "1";
        showRepairPro(currentResult);
      }
    }
"""
s = s.replace("    function showRepairDiy(r) {", toggle + "\n    function showRepairDiy(r) {")

with open(p, "w") as f:
    f.write(s)
print("Reparatie Expert toggle geüpdatet")

# JS check
r = subprocess.run(["node", "-e", "const fs=require('fs');const s=fs.readFileSync('/home/team/shared/backend/templates/index.html','utf8');const m=s.match(/<script>([\\s\\S]*?)<\\/script>/);try{new Function(m[1]);console.log('JS_OK')}catch(e){console.log('Error: '+e.message)}"], capture_output=True, text=True)
print(r.stdout.strip())