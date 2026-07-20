#!/usr/bin/env python3
"""Rewrite showRepairExpert to match the premium clickable flow."""
import subprocess

p = "/home/team/shared/backend/templates/index.html"
with open(p, "r") as f:
    s = f.read()

new_func = """    function showRepairExpert(r) {
      currentResult = r;
      const snapEl = document.getElementById("snapshot");
      currentResultImage = snapEl.src || "";
      const saveBtn = document.getElementById("saveBtn");
      const rc = document.getElementById("resultContent");
      let html = "";
      if (r.is_fallback || r.no_damage || r.warning) { showResults(r); return; }
      const it = r.issue_type || "Reparatie";
      const desc = r.description || "";
      // Diagnose compact + tijdsindicatie / moeilijkheid
      html += '<div class="advice-section" style="margin-bottom:8px">';
      html += '<div class="identify-head" style="font-size:22px;margin-bottom:2px">\\ud83d\\udee0\\ufe0f '+it+'</div>';
      html += '<div style="font-size:13px;color:var(--text-secondary);line-height:1.6;margin-bottom:12px">'+desc+'</div>';
      // Twee klikbare keuzes
      html += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:4px">';
      html += '<div id="repDiyBtn" onclick="showRepairDiy(currentResult)" style="cursor:pointer;padding:16px;border-radius:var(--radius-sm);background:var(--sage-soft);border:1px solid rgba(138,155,122,0.15);text-align:center;transition:all 0.2s">';
      html += '<div style="font-size:20px;margin-bottom:4px">\\ud83d\\udee0\\ufe0f</div>';
      html += '<div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;color:var(--sage);margin-bottom:4px">Zelf repareren</div>';
      // Toon tijdsindicatie als beschikbaar
      if (r.estimate_time) {
        html += '<div style="font-size:22px;font-weight:800;color:var(--sage)">'+r.estimate_time+'</div>';
      } else {
        html += '<div style="font-size:13px;font-weight:600;color:var(--sage)">Stappenplan \\u2192</div>';
      }
      if (r.difficulty) {
        html += '<div style="font-size:11px;color:var(--text-muted);margin-top:2px">'+r.difficulty+'</div>';
      }
      html += '</div>';
      html += '<div id="repProBtn" onclick="showRepairPro(currentResult)" style="cursor:pointer;padding:16px;border-radius:var(--radius-sm);background:var(--terracotta-soft);border:1px solid rgba(196,98,74,0.15);text-align:center;transition:all 0.2s">';
      html += '<div style="font-size:20px;margin-bottom:4px">\\ud83d\\udc77</div>';
      html += '<div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;color:var(--terracotta);margin-bottom:4px">Laten repareren</div>';
      html += '<div style="font-size:13px;font-weight:600;color:var(--terracotta)">Offerte aanvragen \\u2192</div>';
      html += '</div></div>';
      // Container voor de gekozen details
      html += '<div id="repDetail"></div>';
      html += '<div style="height:40px"></div>';
      rc.innerHTML = html;
      saveBtn.style.display = "none";
      currentStep = "diagnose";
    }

    function showRepairDiy(r) {
      const dd = document.getElementById("repDetail");
      let html = '';
      html += '<div style="margin-top:12px;border-radius:var(--radius-sm);border:1px solid rgba(138,155,122,0.2);background:var(--sage-soft);overflow:hidden">';
      html += '<div style="padding:12px 14px;background:var(--sage);color:#fff;font-size:13px;font-weight:700;letter-spacing:0.5px">\\ud83d\\udfe2 Zelf repareren'+(r.estimate_time ? ' \\u2014 '+r.estimate_time : '')+'</div>';
      html += '<div style="padding:14px">';
      // Stappenplan
      if (r.steps && r.steps.length) {
        html += '<div class="advice-subhead" style="font-size:12px;margin-bottom:6px">Stappenplan</div>';
        r.steps.forEach(function(s, i) {
          html += '<div class="step-item"><div class="step-num">'+(i+1)+'</div><div class="step-txt">'+s+'</div></div>';
        });
      }
      // Materialen
      if (r.materials && r.materials.length) {
        html += '<div class="advice-subhead" style="font-size:12px;margin-bottom:6px;margin-top:10px">Materialen</div>';
        html += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-bottom:10px">';
        r.materials.forEach(function(m) {
          html += '<div style="padding:10px 12px;border-radius:8px;background:#fff;border:1px solid rgba(138,155,122,0.15);font-size:12px;color:var(--text-primary);text-align:center;font-weight:500">'+m+'</div>';
        });
        html += '</div>';
        const gammaQ = (r.gamma_tips && r.gamma_tips.length) ? r.gamma_tips.join(", ") : r.materials.join(", ");
        html += '<a class="gamma-link" href="https://www.gamma.nl/zoeken?q='+encodeURIComponent(gammaQ)+'" target="_blank" style="display:flex;align-items:center;justify-content:center;gap:6px;padding:12px;border-radius:8px;font-size:13px;font-weight:700;text-decoration:none;background:#fff;color:var(--sage);border:1.5px solid var(--sage)">\\ud83d\\udecd\\ufe0f Bestel bij Gamma</a>';
      }
      html += '</div></div>';
      html += '<div style="text-align:center;margin-top:8px"><button onclick="showRepairExpert(currentResult)" style="background:none;border:none;color:var(--text-muted);font-size:12px;cursor:pointer;padding:4px 12px">\\u2190 Andere optie</button></div>';
      dd.innerHTML = html;
      document.getElementById("repDiyBtn").style.opacity = "0.6";
      document.getElementById("repProBtn").style.opacity = "1";
    }

    function showRepairPro(r) {
      const dd = document.getElementById("repDetail");
      let html = '';
      html += '<div style="margin-top:12px;border-radius:var(--radius-sm);border:1px solid rgba(196,98,74,0.2);background:var(--terracotta-soft);overflow:hidden">';
      html += '<div style="padding:12px 14px;background:var(--terracotta);color:#fff;font-size:13px;font-weight:700;letter-spacing:0.5px">\\ud83d\\udfe7 Laten repareren</div>';
      html += '<div style="padding:14px">';
      // Rationale - geruststelling
      if (r.pro_rationale) {
        html += '<div style="font-size:13px;color:var(--text-secondary);line-height:1.5;margin-bottom:12px;padding:8px 10px;border-radius:8px;background:rgba(255,255,255,0.5)">'+r.pro_rationale+'</div>';
      } else {
        html += '<div style="font-size:13px;color:var(--text-secondary);line-height:1.5;margin-bottom:12px;padding:8px 10px;border-radius:8px;background:rgba(255,255,255,0.5)">Een vakman heeft de juiste ervaring en gereedschap om dit veilig en duurzaam te repareren.</div>';
      }
      // Vakman
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
      html += '<div style="text-align:center;margin-top:8px"><button onclick="showRepairExpert(currentResult)" style="background:none;border:none;color:var(--text-muted);font-size:12px;cursor:pointer;padding:4px 12px">\\u2190 Andere optie</button></div>';
      dd.innerHTML = html;
      document.getElementById("repProBtn").style.opacity = "0.6";
      document.getElementById("repDiyBtn").style.opacity = "1";
    }"""

# Find showRepairExpert
old_start = "    function showRepairExpert(r) {"
# Next function after it is showDiyRoute (at 0 indent)
next_func = "\nfunction showDiyRoute"
idx_start = s.find(old_start)
idx_end = s.find(next_func, idx_start)
if idx_start < 0 or idx_end < 0:
    print("ERROR: boundaries not found"); exit(1)

s = s[:idx_start] + new_func + "\n" + s[idx_end:]

with open(p, "w") as f:
    f.write(s)

print("showRepairExpert + showRepairDiy + showRepairPro replaced")

r = subprocess.run(["node", "-e", """
const fs=require('fs');
const s=fs.readFileSync('backend/templates/index.html','utf8');
const m=s.match(/<script>([\\s\\S]*?)<\\/script>/);
try{new Function(m[1]);console.log('JS_OK')}catch(e){console.log('JS Error: '+e.message)}
"""], capture_output=True, text=True, cwd="/home/team/shared")
print(r.stdout.strip())