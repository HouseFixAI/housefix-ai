#!/usr/bin/env python3
"""Phase 2: Add showDamageExpert and showRepairExpert functions."""
p = "/home/team/shared/backend/templates/index.html"
with open(p, "r") as f:
    s = f.read()

# ============ showDamageExpert ============
damage_func = """function showDamageExpert(r) {
  currentResult = r;
  const snapEl = document.getElementById("snapshot");
  currentResultImage = snapEl.src || "";
  const saveBtn = document.getElementById("saveBtn");
  const rc = document.getElementById("resultContent");
  let html = "";
  if (r.is_fallback || r.no_damage || r.warning) { showResults(r); return; }
  const it = r.issue_type || "Onbekend";
  const desc = r.description || "";
  const conf = r.confidence || "medium";
  const badgeMap = { high: { c: "badge-high", l: "Hoog" }, medium: { c: "badge-medium", l: "Gemiddeld" }, low: { c: "badge-low", l: "Laag" } };
  const b = badgeMap[conf] || badgeMap.medium;
  // Foto placeholder + type overlay
  html += '<div style="border-radius:var(--radius-sm);overflow:hidden;position:relative;margin-bottom:12px;background:var(--border-light);min-height:180px;display:flex;align-items:center;justify-content:center">';
  if (currentResultImage) {
    html += '<img src="'+currentResultImage+'" style="width:100%;display:block;max-height:220px;object-fit:cover" onerror="this.style.display=\'none\'" />';
  }
  html += '<div style="position:absolute;bottom:0;left:0;right:0;padding:14px 16px;background:linear-gradient(transparent,rgba(0,0,0,0.7))">';
  html += '<div style="font-size:17px;font-weight:700;color:#fff">'+it+'</div>';
  html += '<span class="badge '+b.c+'" style="margin-top:3px">'+b.l+' vertrouwen</span>';
  html += '</div></div>';
  // Diagnose compact
  html += '<div class="advice-section" style="padding-top:0"><div style="font-size:14px;color:var(--text-secondary);line-height:1.6;margin-bottom:8px">'+desc+'</div>';
  // Veiligheid
  if (r.warning) {
    html += '<div style="padding:10px 14px;border-radius:10px;background:rgba(196,98,74,0.06);border:1px solid rgba(196,98,74,0.12);font-size:13px;color:var(--terracotta);line-height:1.5;margin-bottom:12px">\\u26a0\\ufe0f '+r.warning+'</div>';
  }
  // Navigatie naar andere experts
  html += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:4px">';
  html += '<button class="cta-btn" onclick="showRepairExpert(currentResult)" style="padding:12px;font-size:13px;font-weight:600;background:transparent;color:var(--text-primary);border:1.5px solid var(--border-light)">\\ud83d\\udee0\\ufe0f Repareren</button>';
  html += '<button class="cta-btn" onclick="showCostEstimate(currentResult)" style="padding:12px;font-size:13px;font-weight:600;background:transparent;color:var(--text-primary);border:1.5px solid var(--border-light)">\\ud83d\\udcb0 Kosten</button>';
  html += '</div></div>';
  html += '<div style="height:40px"></div>';
  rc.innerHTML = html;
  saveBtn.style.display = "none";
  currentStep = "diagnose";
}"""

# ============ showRepairExpert ============
repair_func = """function showRepairExpert(r) {
  currentResult = r;
  const snapEl = document.getElementById("snapshot");
  currentResultImage = snapEl.src || "";
  const saveBtn = document.getElementById("saveBtn");
  const rc = document.getElementById("resultContent");
  let html = "";
  if (r.is_fallback || r.no_damage || r.warning) { showResults(r); return; }
  const it = r.issue_type || "Reparatie";
  const desc = r.description || "";
  // Stappenplan eerst
  html += '<div class="advice-section"><div class="identify-head" style="font-size:20px;margin-bottom:2px">\\ud83d\\udee0\\ufe0f '+it+'</div>';
  html += '<div style="font-size:13px;color:var(--text-muted);margin-bottom:12px">'+desc+'</div>';
  if (r.steps && r.steps.length) {
    html += '<div class="advice-subhead" style="margin-top:4px">Stappenplan</div>';
    r.steps.forEach(function(s, i) {
      html += '<div class="step-item"><div class="step-num">'+(i+1)+'</div><div class="step-txt">'+s+'</div></div>';
    });
  }
  // Materialen direct onder stappen
  if (r.materials && r.materials.length) {
    html += '<div class="advice-subhead" style="margin-top:12px">Materialen</div><div class="advice-materials">';
    r.materials.forEach(function(m) { html += '<span class="advice-material">'+m+'</span>'; });
    html += '</div>';
    const gammaTips = (r.gamma_tips && r.gamma_tips.length) ? r.gamma_tips.join(", ") : r.materials.join(", ");
    html += '<div style="margin-top:8px"><a class="gamma-link" href="https://www.gamma.nl/zoeken?q='+encodeURIComponent(gammaTips)+'" target="_blank">Bestel bij Gamma</a></div>';
  }
  // Kosten en vakman als secundaire navigatie
  html += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:16px">';
  html += '<button class="cta-btn" onclick="showDamageExpert(currentResult)" style="padding:12px;font-size:13px;font-weight:600;background:transparent;color:var(--text-primary);border:1.5px solid var(--border-light)">\\ud83d\\udd0d Schade</button>';
  html += '<button class="cta-btn" onclick="showCostEstimate(currentResult)" style="padding:12px;font-size:13px;font-weight:600;background:transparent;color:var(--text-primary);border:1.5px solid var(--border-light)">\\ud83d\\udcb0 Kosten</button>';
  html += '</div>';
  // Vakman
  if (providers && providers.length) {
    html += '<div class="advice-divider"></div><div class="advice-subhead">Vakman nodig?</div>';
    html += '<div style="display:flex;flex-wrap:wrap;gap:6px">';
    providers.slice(0,3).forEach(function(p) {
      html += '<a class="wa-link" href="https://wa.me/'+p.phone+'?text=Hallo '+p.name+', ik wil graag een offerte." target="_blank" style="display:inline-flex;align-items:center;gap:4px;padding:8px 14px;border-radius:8px;font-size:12px;font-weight:700;text-decoration:none;background:#1F1E1C;color:#FFF;border:1px solid rgba(255,255,255,0.1)">\\ud83d\\udcac '+p.name+'</a>';
    });
    html += '</div>';
  }
  html += '<div style="height:40px"></div>';
  rc.innerHTML = html;
  saveBtn.style.display = "none";
  currentStep = "diagnose";
}"""

# Find the right insertion point: after showResults function ends, before showDiyRoute
# Search for "}\nfunction showDiyRoute" which marks the end of showResults
target = "}\nfunction showDiyRoute(r) {"
idx = s.find(target)
if idx > 0:
    # Insert damage expert before showDiyRoute
    s = s[:idx] + "\n" + damage_func + "\n" + s[idx:]
    print("showDamageExpert inserted")
else:
    print("ERROR: showDiyRoute not found")

# Now insert showRepairExpert before showDiyRoute as well (after damage expert)
# Actually, let's insert it after showCostEstimate... no, let me find a better spot.
# Insert showRepairExpert between showDamageExpert and showDiyRoute
target2 = "}\nfunction showDiyRoute(r) {"
idx2 = s.find(target2)
if idx2 > 0:
    s = s[:idx2] + "\n" + repair_func + "\n" + s[idx2:]
    print("showRepairExpert inserted")
else:
    print("ERROR: showDiyRoute not found for repair")

with open(p, "w") as f:
    f.write(s)
print("phase2 done")