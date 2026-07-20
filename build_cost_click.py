#!/usr/bin/env python3
"""Make Zelf/Laten sections clickable - only after choosing."""
import subprocess

p = "/home/team/shared/backend/templates/index.html"
with open(p, "r") as f:
    s = f.read()

new_func = """    function showCostEstimate(r) {
      currentResult = r;
      const snapshotEl = document.getElementById("snapshot");
      currentResultImage = snapshotEl.src || "";
      const saveBtn = document.getElementById("saveBtn");
      const resultContent = document.getElementById("resultContent");
      let html = "";
      if (r.is_fallback) {
        html = `<div class="fallback-banner"><span class="fallback-banner-icon">\\u2139\\ufe0f</span> Dit advies is algemeen \\u2014 voor een persoonlijke analyse specifiek voor jouw situatie hebben we een AI-verbinding nodig.</div>`;
        resultContent.innerHTML = html; return;
      }
      if (r.no_damage) {
        html = `<div class="card" style="margin-bottom:14px"><div class="card-body" style="padding:24px;text-align:center"><div style="font-size:20px;font-weight:700;color:var(--sage);margin-bottom:8px">\\u2705 Geen schade</div><div class="res-desc">${r.message || "\\u2705 Geen schade geconstateerd."}</div></div></div>`;
        resultContent.innerHTML = html; return;
      }
      if (r.warning) {
        html = `<div class="card" style="margin-bottom:14px"><div class="card-body" style="padding:24px;text-align:center"><div style="font-size:20px;font-weight:700;color:var(--terracotta);margin-bottom:8px">\\u26a0\\ufe0f Niet herkend</div><div class="res-desc">${r.warning}</div></div></div>`;
        resultContent.innerHTML = html; return;
      }
      const issueType = r.issue_type || "Kosten Schatting";
      const desc = r.description || "";
      const diyCost = r.cost_diy || r.cost_range || "\\u2014";
      const proCost = r.cost_pro || r.cost_range || "\\u2014";
      // Header
      html += `<div class="advice-section" style="margin-bottom:8px">`;
      html += `<div class="identify-head" style="font-size:22px;margin-bottom:2px">${issueType}</div>`;
      html += `<div class="identify-context" style="font-size:13px;margin-bottom:12px">${desc}</div>`;
      // Kosten blokken - klikbaar, worden de navigatie
      html += `<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:4px">`;
      if (diyCost !== "\\u2014") {
        html += `<div id="costDiyBtn" onclick="showCostDiy(currentResult)" style="cursor:pointer;padding:16px;border-radius:var(--radius-sm);background:var(--sage-soft);border:1px solid rgba(138,155,122,0.15);text-align:center;transition:all 0.2s"><div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;color:var(--sage);margin-bottom:4px">Zelf doen</div><div style="font-size:22px;font-weight:800;color:var(--sage)">${diyCost}</div><div style="font-size:11px;color:var(--text-muted);margin-top:2px">alleen materiaal \\u2192</div></div>`;
      }
      if (proCost !== "\\u2014") {
        html += `<div id="costProBtn" onclick="showCostPro(currentResult)" style="cursor:pointer;padding:16px;border-radius:var(--radius-sm);background:var(--terracotta-soft);border:1px solid rgba(196,98,74,0.15);text-align:center;transition:all 0.2s"><div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;color:var(--terracotta);margin-bottom:4px">Laten doen</div><div style="font-size:22px;font-weight:800;color:var(--terracotta)">${proCost}</div><div style="font-size:11px;color:var(--text-muted);margin-top:2px">incl. voorrijkosten \\u2192</div></div>`;
      }
      html += `</div>`;
      // Container waar de gekozen sectie wordt ingeladen
      html += `<div id="costDetail"></div>`;
      html += `<div style="height:40px"></div>`;
      resultContent.innerHTML = html;
      saveBtn.style.display = "none";
      currentStep = "diagnose";
    }

    function showCostDiy(r) {
      currentResult = r;
      const dd = document.getElementById("costDetail");
      const diyCost = r.cost_diy || r.cost_range || "\\u2014";
      let html = "";
      html += `<div style="margin-top:12px;border-radius:var(--radius-sm);border:1px solid rgba(138,155,122,0.2);background:var(--sage-soft);overflow:hidden">`;
      html += `<div style="padding:12px 14px;background:var(--sage);color:#fff;font-size:13px;font-weight:700;letter-spacing:0.5px">\\ud83d\\udfe2 Zelf doen \\u2014 ${diyCost}</div>`;
      html += `<div style="padding:14px">`;
      if (r.diy_rationale) {
        html += `<div style="font-size:13px;color:var(--text-secondary);line-height:1.5;margin-bottom:12px;padding:8px 10px;border-radius:8px;background:rgba(255,255,255,0.5)">${r.diy_rationale}</div>`;
      }
      if (r.steps && r.steps.length) {
        html += `<div class="advice-subhead" style="font-size:12px;margin-bottom:6px">Stappenplan</div>`;
        r.steps.forEach(function(s, i) {
          html += `<div class="step-item"><div class="step-num">${i+1}</div><div class="step-txt">${s}</div></div>`;
        });
      }
      if (r.materials && r.materials.length) {
        html += `<div class="advice-subhead" style="font-size:12px;margin-bottom:6px;margin-top:10px">Materialen</div>`;
        html += `<div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-bottom:10px">`;
        r.materials.forEach(function(m) {
          html += `<div style="padding:10px 12px;border-radius:8px;background:#fff;border:1px solid rgba(138,155,122,0.15);font-size:12px;color:var(--text-primary);text-align:center;font-weight:500">${m}</div>`;
        });
        html += `</div>`;
        const gammaQ = (r.gamma_tips && r.gamma_tips.length) ? r.gamma_tips.join(", ") : r.materials.join(", ");
        html += `<a class="gamma-link" href="https://www.gamma.nl/zoeken?q=${encodeURIComponent(gammaQ)}" target="_blank" style="display:flex;align-items:center;justify-content:center;gap:6px;padding:12px;border-radius:8px;font-size:13px;font-weight:700;text-decoration:none;background:#fff;color:var(--sage);border:1.5px solid var(--sage)">\\ud83d\\udecd\\ufe0f Bestel bij Gamma</a>`;
      }
      // Video placeholder
      html += `<div style="height:4px"></div>`;
      html += `</div></div>`;
      html += `<div style="text-align:center;margin-top:8px"><button onclick="showCostEstimate(currentResult)" style="background:none;border:none;color:var(--text-muted);font-size:12px;cursor:pointer;padding:4px 12px">\\u2190 Andere optie</button></div>`;
      dd.innerHTML = html;
      document.getElementById("costDiyBtn").style.opacity = "0.6";
      document.getElementById("costProBtn").style.opacity = "1";
    }

    function showCostPro(r) {
      currentResult = r;
      const dd = document.getElementById("costDetail");
      const proCost = r.cost_pro || r.cost_range || "\\u2014";
      let html = "";
      html += `<div style="margin-top:12px;border-radius:var(--radius-sm);border:1px solid rgba(196,98,74,0.2);background:var(--terracotta-soft);overflow:hidden">`;
      html += `<div style="padding:12px 14px;background:var(--terracotta);color:#fff;font-size:13px;font-weight:700;letter-spacing:0.5px">\\ud83d\\udfe7 Laten doen \\u2014 ${proCost}</div>`;
      html += `<div style="padding:14px">`;
      if (r.pro_rationale) {
        html += `<div style="font-size:13px;color:var(--text-secondary);line-height:1.5;margin-bottom:12px;padding:8px 10px;border-radius:8px;background:rgba(255,255,255,0.5)">${r.pro_rationale}</div>`;
      }
      if (providers && providers.length) {
        html += `<div class="advice-subhead" style="font-size:12px;margin-bottom:6px">Vakman in de buurt</div>`;
        html += `<div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:10px">`;
        providers.slice(0,3).forEach(function(p) {
          const full = Math.floor(p.rating);
          const half = p.rating % 1 >= 0.5;
          html += `<div style="flex:1;min-width:140px;padding:10px 12px;border-radius:8px;background:#fff;border:1px solid rgba(196,98,74,0.12);text-align:center">`;
          html += `<div style="font-size:13px;font-weight:700;color:var(--text-primary);margin-bottom:2px">${p.name}</div>`;
          html += `<div style="font-size:11px;color:#d4a847;margin-bottom:4px">${'\\u2605'.repeat(full)}${half ? '\\u00bd' : ''}</div>`;
          html += `<div style="font-size:10px;color:var(--text-muted);margin-bottom:6px">${p.city} \\u00b7 ${p.category}</div>`;
          html += `<a class="wa-link" href="https://wa.me/${p.phone}?text=Hallo ${p.name}, ik wil graag een offerte." target="_blank" style="display:block;padding:8px;border-radius:6px;font-size:12px;font-weight:700;text-decoration:none;background:#1F1E1C;color:#FFF;letter-spacing:0.5px">\\ud83d\\udcac Offerte</a>`;
          html += `</div>`;
        });
        html += `</div>`;
        if (providers.length > 3) {
          html += `<button class="cta-btn" onclick="renderProviders()" style="width:100%;padding:10px;font-size:12px;font-weight:600;background:transparent;color:var(--terracotta);border:1px solid var(--terracotta);border-radius:8px">Vergelijk alle ${providers.length} bedrijven \\u2192</button>`;
        }
      }
      html += `</div></div>`;
      html += `<div style="text-align:center;margin-top:8px"><button onclick="showCostEstimate(currentResult)" style="background:none;border:none;color:var(--text-muted);font-size:12px;cursor:pointer;padding:4px 12px">\\u2190 Andere optie</button></div>`;
      dd.innerHTML = html;
      document.getElementById("costProBtn").style.opacity = "0.6";
      document.getElementById("costDiyBtn").style.opacity = "1";
    }"""

# Find the old function
old_start = "    function showCostEstimate(r) {"
next_func = "    function renderColorPalette"
idx_start = s.find(old_start)
idx_end = s.find(next_func, idx_start)
if idx_start < 0 or idx_end < 0:
    print("ERROR: boundaries not found"); exit(1)

s = s[:idx_start] + new_func + "\n\n" + s[idx_end:]

with open(p, "w") as f:
    f.write(s)
print("showCostEstimate + showCostDiy + showCostPro replaced")

# JS check
r = subprocess.run(["node", "-e", """
const fs=require('fs');
const s=fs.readFileSync('backend/templates/index.html','utf8');
const m=s.match(/<script>([\\s\\S]*?)<\\/script>/);
try{new Function(m[1]);console.log('JS_OK')}catch(e){console.log('JS Error: '+e.message)}
"""], capture_output=True, text=True, cwd="/home/team/shared")
print(r.stdout.strip())