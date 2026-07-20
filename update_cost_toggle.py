#!/usr/bin/env python3
"""Kosten Expert: toggle-functionaliteit (klik=toon, nogmaals=weg), geen terug-link."""
import subprocess

p = "/home/team/shared/backend/templates/index.html"
with open(p, "r") as f:
    s = f.read()

# ── 1. showCostEstimate: onclick naar toggle, emoji/stijl intact ──
old = '''      // Kosten blokken - klikbaar, worden de navigatie
      html += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:4px">';
      if (diyCost !== "\\u2014") {
        html += '<div id="costDiyBtn" onclick="showCostDiy(currentResult)" style="cursor:pointer;padding:16px;border-radius:var(--radius-sm);background:var(--sage-soft);border:1px solid rgba(138,155,122,0.15);text-align:center;transition:all 0.2s"><div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;color:var(--sage);margin-bottom:4px">Zelf doen</div><div style="font-size:22px;font-weight:800;color:var(--sage)">${diyCost}</div><div style="font-size:11px;color:var(--text-muted);margin-top:2px">alleen materiaal \\u2192</div></div>';
      }
      if (proCost !== "\\u2014") {
        html += '<div id="costProBtn" onclick="showCostPro(currentResult)" style="cursor:pointer;padding:16px;border-radius:var(--radius-sm);background:var(--terracotta-soft);border:1px solid rgba(196,98,74,0.15);text-align:center;transition:all 0.2s"><div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;color:var(--terracotta);margin-bottom:4px">Laten doen</div><div style="font-size:22px;font-weight:800;color:var(--terracotta)">${proCost}</div><div style="font-size:11px;color:var(--text-muted);margin-top:2px">incl. voorrijkosten \\u2192</div></div>';
      }
      html += '</div>';'''

new = '''      // Kosten blokken - toggle knoppen
      html += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:4px">';
      if (diyCost !== "\\u2014") {
        html += '<div id="costDiyBtn" onclick="toggleCostSection(\\'diy\\')" style="cursor:pointer;padding:16px;border-radius:var(--radius-sm);background:var(--sage-soft);border:1px solid rgba(138,155,122,0.15);text-align:center;transition:all 0.2s"><div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;color:var(--sage);margin-bottom:4px">Zelf doen</div><div style="font-size:22px;font-weight:800;color:var(--sage)">${diyCost}</div><div style="font-size:11px;color:var(--text-muted);margin-top:2px">alleen materiaal</div></div>';
      }
      if (proCost !== "\\u2014") {
        html += '<div id="costProBtn" onclick="toggleCostSection(\\'pro\\')" style="cursor:pointer;padding:16px;border-radius:var(--radius-sm);background:var(--terracotta-soft);border:1px solid rgba(196,98,74,0.15);text-align:center;transition:all 0.2s"><div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;color:var(--terracotta);margin-bottom:4px">Laten doen</div><div style="font-size:22px;font-weight:800;color:var(--terracotta)">${proCost}</div><div style="font-size:11px;color:var(--text-muted);margin-top:2px">incl. voorrijkosten</div></div>';
      }
      html += '</div>';'''

s = s.replace(old, new)

# ── 2. showCostDiy: verwijder "Andere optie" link ──
old_diy = '''      html += '<div style="text-align:center;margin-top:8px"><button onclick="showCostEstimate(currentResult)" style="background:none;border:none;color:var(--text-muted);font-size:12px;cursor:pointer;padding:4px 12px">\\u2190 Andere optie</button></div>';
      dd.innerHTML = html;
      document.getElementById("costDiyBtn").style.opacity = "0.6";
      document.getElementById("costProBtn").style.opacity = "1";
    }

    function showCostPro'''

new_diy = '''      dd.innerHTML = html;
      document.getElementById("costDiyBtn").style.opacity = "0.6";
      document.getElementById("costProBtn").style.opacity = "1";
    }

    function showCostPro'''

s = s.replace(old_diy, new_diy)

# ── 3. showCostPro: verwijder "Andere optie" link ──
old_pro = '''    function showCostPro(r) {
      currentResult = r;
      const dd = document.getElementById("costDetail");
      const proCost = r.cost_pro || r.cost_range || "\\u2014";
      let html = "";
      html += '<div style="margin-top:12px;border-radius:var(--radius-sm);border:1px solid rgba(196,98,74,0.2);background:var(--terracotta-soft);overflow:hidden">';
      html += '<div style="padding:12px 14px;background:var(--terracotta);color:#fff;font-size:13px;font-weight:700;letter-spacing:0.5px">\\ud83d\\udfe7 Laten doen \\u2014 ${proCost}</div>';
      html += '<div style="padding:14px">';
      if (r.pro_rationale) {
        html += '<div style="font-size:13px;color:var(--text-secondary);line-height:1.5;margin-bottom:12px;padding:8px 10px;border-radius:8px;background:rgba(255,255,255,0.5)">'+r.pro_rationale+'</div>';
      }
      if (providers && providers.length) {
        html += '<div class="advice-subhead" style="font-size:12px;margin-bottom:6px">Vakman in de buurt</div>';
        html += '<div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:10px">';
        providers.slice(0,3).forEach(function(p) {
          const full = Math.floor(p.rating);
          const half = p.rating % 1 >= 0.5;
          html += '<div style="flex:1;min-width:140px;padding:10px 12px;border-radius:8px;background:#fff;border:1px solid rgba(196,98,74,0.12);text-align:center">';
          html += '<div style="font-size:13px;font-weight:700;color:var(--text-primary);margin-bottom:2px">'+p.name+'</div>';
          html += '<div style="font-size:11px;color:#d4a847;margin-bottom:4px">'+'\\u2605'.repeat(full)+(half?'\\u00bd':'')+'</div>';
          html += '<div style="font-size:10px;color:var(--text-muted);margin-bottom:6px">'+p.city+' \\u00b7 '+p.category+'</div>';
          html += '<a class="wa-link" href="https://wa.me/'+p.phone+'?text=Hallo '+p.name+', ik wil graag een offerte." target="_blank" style="display:block;padding:8px;border-radius:6px;font-size:12px;font-weight:700;text-decoration:none;background:#1F1E1C;color:#FFF;letter-spacing:0.5px">\\ud83d\\udcac Offerte</a>';
          html += '</div>';
        });
        html += '</div>';
        if (providers.length > 3) {
          html += '<button class="cta-btn" onclick="renderProviders()" style="width:100%;padding:10px;font-size:12px;font-weight:600;background:transparent;color:var(--terracotta);border:1px solid var(--terracotta);border-radius:8px">Vergelijk alle '+providers.length+' bedrijven \\u2192</button>';
        }
      }
      html += '</div></div>';
      html += '<div style="text-align:center;margin-top:8px"><button onclick="showCostEstimate(currentResult)" style="background:none;border:none;color:var(--text-muted);font-size:12px;cursor:pointer;padding:4px 12px">\\u2190 Andere optie</button></div>';
      dd.innerHTML = html;
      document.getElementById("costProBtn").style.opacity = "0.6";
      document.getElementById("costDiyBtn").style.opacity = "1";
    }'''

new_pro = '''    function showCostPro(r) {
      currentResult = r;
      const dd = document.getElementById("costDetail");
      const proCost = r.cost_pro || r.cost_range || "\\u2014";
      let html = "";
      html += '<div style="margin-top:12px;border-radius:var(--radius-sm);border:1px solid rgba(196,98,74,0.2);background:var(--terracotta-soft);overflow:hidden">';
      html += '<div style="padding:12px 14px;background:var(--terracotta);color:#fff;font-size:13px;font-weight:700;letter-spacing:0.5px">\\ud83d\\udfe7 Laten doen \\u2014 ${proCost}</div>';
      html += '<div style="padding:14px">';
      if (r.pro_rationale) {
        html += '<div style="font-size:13px;color:var(--text-secondary);line-height:1.5;margin-bottom:12px;padding:8px 10px;border-radius:8px;background:rgba(255,255,255,0.5)">'+r.pro_rationale+'</div>';
      }
      if (providers && providers.length) {
        html += '<div class="advice-subhead" style="font-size:12px;margin-bottom:6px">Vakman in de buurt</div>';
        html += '<div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:10px">';
        providers.slice(0,3).forEach(function(p) {
          const full = Math.floor(p.rating);
          const half = p.rating % 1 >= 0.5;
          html += '<div style="flex:1;min-width:140px;padding:10px 12px;border-radius:8px;background:#fff;border:1px solid rgba(196,98,74,0.12);text-align:center">';
          html += '<div style="font-size:13px;font-weight:700;color:var(--text-primary);margin-bottom:2px">'+p.name+'</div>';
          html += '<div style="font-size:11px;color:#d4a847;margin-bottom:4px">'+'\\u2605'.repeat(full)+(half?'\\u00bd':'')+'</div>';
          html += '<div style="font-size:10px;color:var(--text-muted);margin-bottom:6px">'+p.city+' \\u00b7 '+p.category+'</div>';
          html += '<a class="wa-link" href="https://wa.me/'+p.phone+'?text=Hallo '+p.name+', ik wil graag een offerte." target="_blank" style="display:block;padding:8px;border-radius:6px;font-size:12px;font-weight:700;text-decoration:none;background:#1F1E1C;color:#FFF;letter-spacing:0.5px">\\ud83d\\udcac Offerte</a>';
          html += '</div>';
        });
        html += '</div>';
        if (providers.length > 3) {
          html += '<button class="cta-btn" onclick="renderProviders()" style="width:100%;padding:10px;font-size:12px;font-weight:600;background:transparent;color:var(--terracotta);border:1px solid var(--terracotta);border-radius:8px">Vergelijk alle '+providers.length+' bedrijven \\u2192</button>';
        }
      }
      html += '</div></div>';
      dd.innerHTML = html;
      document.getElementById("costProBtn").style.opacity = "0.6";
      document.getElementById("costDiyBtn").style.opacity = "1";
    }'''

s = s.replace(old_pro, new_pro)

# ── 4. Voeg toggleCostSection toe ──
toggle_func = """
    var _costSectionOpen = null;
    function toggleCostSection(section) {
      if (_costSectionOpen === section) {
        document.getElementById("costDetail").innerHTML = '';
        document.getElementById("costDiyBtn").style.opacity = "1";
        document.getElementById("costProBtn").style.opacity = "1";
        _costSectionOpen = null;
        return;
      }
      _costSectionOpen = section;
      if (section === 'diy') {
        document.getElementById("costDiyBtn").style.opacity = "0.6";
        document.getElementById("costProBtn").style.opacity = "1";
        showCostDiy(currentResult);
      } else {
        document.getElementById("costProBtn").style.opacity = "0.6";
        document.getElementById("costDiyBtn").style.opacity = "1";
        showCostPro(currentResult);
      }
    }
"""

# Insert after showCostEstimate function closes (before showCostDiy)
old_marker = "    function showCostDiy"
s = s.replace(old_marker, toggle_func + "\n" + old_marker, 1)

with open(p, "w") as f:
    f.write(s)
print("Kosten Expert toggle geüpdatet")

# JS check
r = subprocess.run(["node", "-e", """
const fs=require('fs');
const s=fs.readFileSync('/home/team/shared/backend/templates/index.html','utf8');
const m=s.match(/<script>([\\s\\S]*?)<\\/script>/);
try{new Function(m[1]);console.log('JS_OK')}catch(e){console.log('Error: '+e.message)}
"""], capture_output=True, text=True)
print(r.stdout.strip())