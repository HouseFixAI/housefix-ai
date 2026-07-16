#!/usr/bin/env python3
"""Split Klus Hulp into step-by-step flow. No external files, no surrogates."""

path = "/home/team/shared/backend/templates/index.html"
with open(path, "r", encoding="utf-8") as f:
    html = f.read()

# Find showResults function
start_marker = "function showResults(r) {"
end_marker = "\nfunction renderProviders("
start_idx = html.find(start_marker)
end_idx = html.find(end_marker, start_idx)
if start_idx < 0 or end_idx < 0:
    print("ERROR: markers not found")
    exit(1)

func_start = html.rfind("\n", 0, start_idx) + 1
func_end = end_idx

# New showResults + showDiyRoute + showProRoute
# Uses only ASCII-safe \\uXXXX escapes for JS
new_funcs = """function showResults(r) {
  currentResult = r;
  const snapshotEl = document.getElementById("snapshot");
  currentResultImage = snapshotEl.src || "";
  const saveBtn = document.getElementById("saveBtn");
  const resultContent = document.getElementById("resultContent");
  let html = "";
  if (r.is_fallback) {
    html = `<div class="fallback-banner"><span class="fallback-banner-icon">\\u2139\\ufe0f</span> Dit advies is algemeen \\u2014 voor een persoonlijke analyse specifiek voor jouw situatie hebben we een AI-verbinding nodig.</div>`;
  }
  if (r.no_damage) {
    html += `<div class="card" style="margin-bottom:14px"><div class="card-body" style="padding:24px;text-align:center"><div style="font-size:20px;font-weight:700;color:var(--sage);margin-bottom:8px">\\u2705 Geen schade</div><div class="res-desc">${r.message || "\\u2705 Geen schade geconstateerd. Deze muur/oppervlak ziet er constructief goed uit. Er is geen reparatie nodig."}</div></div></div>`;
    resultContent.innerHTML = html;
    return;
  }
  if (r.warning) {
    html += `<div class="card" style="margin-bottom:14px"><div class="card-body" style="padding:24px;text-align:center"><div style="font-size:20px;font-weight:700;color:var(--terracotta);margin-bottom:8px">\\u26a0\\ufe0f Niet herkend</div><div class="res-desc">${r.warning}</div></div></div>`;
    resultContent.innerHTML = html;
    return;
  }
  if (currentMode === "inspiration" && r.style) {
    document.getElementById("issueCard").style.display = "block";
    document.getElementById("resultThumb").src = document.getElementById("snapshot").src;
    document.getElementById("resultType").textContent = r.style;
    document.getElementById("resultDesc").textContent = r.description || "";
    const conf = r.confidence || "medium";
    const b = { high: { c: "badge-high", l: "Hoog" }, medium: { c: "badge-medium", l: "Gemiddeld" }, low: { c: "badge-low", l: "Laag" } }[conf] || { c: "badge-medium", l: "Gemiddeld" };
    document.getElementById("resultBadge").innerHTML = `<span class="badge ${b.c}">${b.l}</span>`;
    if (r.similar_styles && r.similar_styles.length) {
      const ssHtml = r.similar_styles.map(s => `<span class="material-tag">${s}</span>`).join("");
      document.getElementById("resultType").innerHTML = r.style + ' <span style="font-size:12px;color:var(--text-muted);font-weight:400;display:block;margin-top:2px">' + ssHtml + '</span>';
    }
    if (r.colors && r.colors.length) {
      document.getElementById("costCard").style.display = "block";
      document.getElementById("costCard").querySelector(".card-header").innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0"><circle cx="13.5" cy="6.5" r=".5" fill="currentColor"/><circle cx="17.5" cy="10.5" r=".5" fill="currentColor"/><circle cx="8.5" cy="7.5" r=".5" fill="currentColor"/><circle cx="6.5" cy="12.5" r=".5" fill="currentColor"/><path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c.926 0 1.648-.746 1.648-1.688 0-.437-.18-.835-.437-1.125-.29-.289-.438-.652-.438-1.125a1.64 1.64 0 0 1 1.668-1.668h1.996c3.051 0 5.555-2.503 5.555-5.554C21.965 6.012 17.461 2 12 2z"/></svg> Kleurenpalet';
      document.querySelector(".cost-box.diy .cost-label").textContent = "Kleuren";
      const colorHex = {'wit':'#ffffff','beige':'#f5f0e1','cr\\u00e8me':'#fff8e7','zand':'#d4c5a9','grijs':'#9e9e9e','antraciet':'#404040','zwart':'#222222','bruin':'#8d6e63','koffie':'#6d4c41','taupe':'#b8a99a','groen':'#66bb6a','olijfgroen':'#8d9b6a','mint':'#a5d6a7','saliegroen':'#b5c9a3','blauw':'#64b5f6','lichtblauw':'#90caf9','donkerblauw':'#3949ab','navy':'#1a237e','rood':'#e57373','bordeaux':'#8e2430','roze':'#f48fb1','lichtroze':'#f8bbd0','geel':'#ffd54f','mosterd':'#f4c842','oranje':'#ffb74d','koper':'#d4935a','paars':'#ab47bc','lila':'#ce93d8','goud':'#d4a847','zilver':'#bdbdbd','hout':'#a58a6f','naturel':'#d4c4a8'};
      const swatches = r.colors.map(c => {const low=c.toLowerCase();let hex='#cccccc';for(const[key,val]of Object.entries(colorHex)){if(low.includes(key)){hex=val;break}}return`<span class="color-swatch"><span class="color-dot" style="background:${hex};${hex==='#ffffff'?'border:1px solid rgba(255,255,255,0.2)':''}"></span>${c}</span>`}).join(' ');
      document.getElementById("costDiy").innerHTML = swatches;
      document.getElementById("costPro").textContent = "";
      document.getElementById("costPro").parentElement.style.display = "none";
    } else { document.getElementById("costCard").style.display = "none"; }
    if (r.styling_tip) { document.getElementById("saveBtn").textContent = r.styling_tip; document.getElementById("saveBtn").classList.add("saved"); }
    if (r.materials && r.materials.length) {
      document.getElementById("materialsCard").style.display = "block";
      document.getElementById("materialsCard").querySelector(".card-header").innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/></svg> Materialen';
      document.getElementById("materialsBody").innerHTML = r.materials.map(m => `<span class="material-tag">${m}</span>`).join("");
      document.getElementById("gammaLink").parentElement.style.display = "block";
      if (r.gamma_tips && r.gamma_tips.length) { document.getElementById("gammaLink").href = `https://www.gamma.nl/zoeken?q=${encodeURIComponent(r.gamma_tips.join(", "))}`; }
    } else { document.getElementById("materialsCard").style.display = "none"; }
    if (r.matching_stores && r.matching_stores.length) {
      document.getElementById("stepsCard").style.display = "block";
      document.getElementById("stepsCard").querySelector(".card-header").innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0"><path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/><line x1="3" y1="6" x2="21" y2="6"/><path d="M16 10a4 4 0 0 1-8 0"/></svg> Shopadvies';
      document.getElementById("stepsBody").innerHTML = r.matching_stores.map(s => `<div class="step-item"><div class="step-num">\\U0001F3EA</div><div class="step-txt">${s}</div></div>`).join("");
    } else { document.getElementById("stepsCard").style.display = "none"; }
    document.getElementById("providersCard").style.display = "none";
    return;
  }
  const issueType = r.issue_type || "Onbekend";
  const desc = r.description || "";
  const conf = r.confidence || "medium";
  const badgeMap = { high: { c: "badge-high", l: "Hoog" }, medium: { c: "badge-medium", l: "Gemiddeld" }, low: { c: "badge-low", l: "Laag" } };
  const b = badgeMap[conf] || badgeMap.medium;
  html += `<div class="advice-section">`;
  html += `<div class="identify-head">${issueType}</div>`;
  html += `<div class="identify-sub">${b.l} vertrouwen</div>`;
  html += `<div class="identify-context">${desc}</div>`;
  if (r.warning) {
    html += `<div style="padding:12px 16px;border-radius:12px;background:rgba(196,98,74,0.06);border:1px solid rgba(196,98,74,0.12);font-size:14px;color:var(--terracotta);line-height:1.5;margin-bottom:16px">\\u26a0\\ufe0f ${r.warning}</div>`;
  }
  html += `<div style="margin-top:20px;display:flex;flex-direction:column;gap:10px">`;
  html += `<button class="cta-btn" onclick="showDiyRoute(currentResult)" style="padding:16px;font-size:16px">\\uD83D\\uDEE0\\uFE0F  Zelf doen</button>`;
  html += `<button class="cta-btn" onclick="showProRoute(currentResult)" style="padding:16px;font-size:16px;background:transparent;color:var(--text-primary);border:1.5px solid var(--border-light)">\\uD83D\\uDC77  Laten doen</button>`;
  html += `</div></div>`;
  resultContent.innerHTML = html;
  saveBtn.style.display = "none";
}
function showDiyRoute(r) {
  const resultContent = document.getElementById("resultContent");
  const saveBtn = document.getElementById("saveBtn");
  const diyCost = r.cost_diy || r.cost_range || "\\u2014";
  let html = `<div style="margin-bottom:12px"><button class="header-btn" onclick="showResults(currentResult)" style="color:var(--terracotta);font-size:13px;padding:6px 0;width:auto;gap:4px">\\u2B05\\uFE0F  Terug naar diagnose</button></div>`;
  if (diyCost !== "\\u2014") {
    html += `<div class="advice-section"><div class="advice-subhead">Kosten</div>`;
    html += `<div style="padding:16px;border-radius:var(--radius-sm);background:var(--sage-soft);border:1px solid rgba(138,155,122,0.15);text-align:center"><div style="font-size:24px;font-weight:800;color:var(--sage)">${diyCost}</div><div style="font-size:12px;color:var(--text-muted);margin-top:3px">alleen materiaal</div></div></div>`;
  }
  if (r.steps && r.steps.length) {
    html += `<div class="advice-divider"></div>`;
    html += `<div class="advice-section"><div class="advice-subhead">Stappenplan</div>`;
    r.steps.forEach((s, i) => { html += `<div class="step-item"><div class="step-num">${i+1}</div><div class="step-txt">${s}</div></div>`; });
    html += `</div>`;
  }
  if (r.materials && r.materials.length) {
    html += `<div class="advice-divider"></div>`;
    html += `<div class="advice-section"><div class="advice-subhead">Materialen</div><div class="advice-materials">`;
    r.materials.forEach(m => { html += `<span class="advice-material">${m}</span>`; });
    html += `</div>`;
    const gammaTips = (r.gamma_tips && r.gamma_tips.length) ? r.gamma_tips.join(", ") : r.materials.join(", ");
    html += `<div style="margin-top:10px"><a class="gamma-link" href="https://www.gamma.nl/zoeken?q=${encodeURIComponent(gammaTips)}" target="_blank">Bestel bij Gamma</a></div>`;
    html += `</div>`;
  }
  html += `<div class="advice-divider"></div>`;
  html += `<div style="display:flex;flex-direction:column;gap:8px;padding-bottom:20px">`;
  html += `<button class="header-btn" onclick="showResults(currentResult)" style="color:var(--terracotta);font-size:14px;padding:10px 0;width:100%;gap:6px">\\u2B05\\uFE0F  Terug naar diagnose</button>`;
  html += `<button class="footer-btn-secondary" onclick="goHome()" style="text-align:center">Nieuwe scan</button>`;
  html += `<button class="footer-btn-secondary" onclick="goHome()" style="text-align:center">Home</button>`;
  html += `</div>`;
  resultContent.innerHTML = html;
  saveBtn.style.display = "none";
}
function showProRoute(r) {
  const resultContent = document.getElementById("resultContent");
  const saveBtn = document.getElementById("saveBtn");
  const proCost = r.cost_pro || r.cost_range || "\\u2014";
  let html = `<div style="margin-bottom:12px"><button class="header-btn" onclick="showResults(currentResult)" style="color:var(--terracotta);font-size:13px;padding:6px 0;width:auto;gap:4px">\\u2B05\\uFE0F  Terug naar diagnose</button></div>`;
  if (proCost !== "\\u2014") {
    html += `<div class="advice-section"><div class="advice-subhead">Kosten</div>`;
    html += `<div style="padding:16px;border-radius:var(--radius-sm);background:var(--terracotta-soft);border:1px solid rgba(196,98,74,0.15);text-align:center"><div style="font-size:24px;font-weight:800;color:var(--terracotta)">${proCost}</div><div style="font-size:12px;color:var(--text-muted);margin-top:3px">incl. voorrijkosten</div></div></div>`;
  }
  if (providers && providers.length) {
    html += `<div class="advice-divider"></div>`;
    html += `<div class="advice-section"><div class="advice-subhead">Professionals in jouw buurt</div>`;
    html += `<div class="filter-bar" id="provFilters" style="padding:0 0 12px 0"></div>`;
    html += `<div class="prov-grid" id="provGrid"></div>`;
    html += `</div>`;
  }
  html += `<div class="advice-divider"></div>`;
  html += `<div style="display:flex;flex-direction:column;gap:8px;padding-bottom:20px">`;
  html += `<button class="header-btn" onclick="showResults(currentResult)" style="color:var(--terracotta);font-size:14px;padding:10px 0;width:100%;gap:6px">\\u2B05\\uFE0F  Terug naar diagnose</button>`;
  html += `<button class="footer-btn-secondary" onclick="goHome()" style="text-align:center">Nieuwe scan</button>`;
  html += `<button class="footer-btn-secondary" onclick="goHome()" style="text-align:center">Home</button>`;
  html += `</div>`;
  resultContent.innerHTML = html;
  saveBtn.style.display = "none";
  if (providers && providers.length) renderProviders();
}
"""

# Replace
html = html[:func_start] + new_funcs + html[func_end:]

# Replace renderProviders
old_rp = """function renderProviders(filter) {
  const list = filter ? providers.filter(p => p.category === filter) : providers;
  const cats = ["Alles", ...new Set(providers.map(p => p.category))];
  const fEl = document.getElementById("provFilters");
  const gEl = document.getElementById("provGrid");
  if (!fEl || !gEl) return;
  fEl.innerHTML = cats.map(c =>
    `<button class="filter-btn ${c === (filter || 'Alles') ? 'active' : ''}" onclick="renderProviders('${c === 'Alles' ? '' : c}')">${c}</button>`
  ).join("");
  gEl.innerHTML = list.map(p => {
    const full = Math.floor(p.rating);
    const half = p.rating % 1 >= 0.5;
    return `<div class="purchase-card" style="margin-bottom:10px;padding:14px">
      <div style="font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;color:var(--sage);margin-bottom:2px">${p.category}</div>
      <div class="purchase-card-name">${p.name}</div>
      <div style="font-size:12px;color:var(--text-muted);margin-bottom:10px"><span style="color:#d4a847">${'\\u2605'.repeat(full)}${half ? '\\u00BD' : ''}</span> ${p.city}</div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px">
        <a class="wa-link" href="https://wa.me/${p.phone}?text=Hallo ${p.name}, ik heb via HouseFix AI een klus en wil graag een offerte." target="_blank" style="display:flex;align-items:center;justify-content:center;gap:4px;padding:10px;border-radius:8px;font-size:12px;font-weight:700;text-decoration:none;background:#1F1E1C;color:#FFFFFF;border:1px solid rgba(255,255,255,0.1);letter-spacing:0.5px;transition:all 0.2s">\\u2728 WhatsApp</a>
        <button onclick="alert('Offerte aanvragen is binnenkort beschikbaar!')" style="display:flex;align-items:center;justify-content:center;gap:4px;padding:10px;border-radius:8px;font-size:12px;font-weight:700;border:1px solid var(--border-light);background:var(--bg-card);color:var(--text-secondary);cursor:pointer;transition:all 0.2s">\\uD83D\\uDCCB Offerte</button>
      </div>
    </div>`;
  }).join("");
}"""

# Find and replace renderProviders
rp_start = html.find("function renderProviders(")
rp_end = html.find("\\n\\n", rp_start) if html.find("\\n\\n", rp_start) > 0 else html.find("\\n/*", rp_start)
if rp_start > 0:
    # Find end of function (blank line or next comment)
    search_from = rp_start
    for end_pos in range(rp_start, len(html)):
        if html[end_pos:end_pos+2] == "\\n\\n" or html[end_pos:end_pos+3] == "\\n/*":
            rp_end = end_pos
            break
    else:
        rp_end = html.find("\\n\\n", rp_start)
    if rp_end <= rp_start:
        rp_end = len(html)
    # Get the actual content
    old_rp_actual = html[rp_start:rp_end]
    # Replace with new version
    new_rp = """function renderProviders(filter) {
  const list = filter ? providers.filter(p => p.category === filter) : providers;
  const cats = ["Alles", ...new Set(providers.map(p => p.category))];
  const fEl = document.getElementById("provFilters");
  const gEl = document.getElementById("provGrid");
  if (!fEl || !gEl) return;
  fEl.innerHTML = cats.map(c =>
    `<button class="filter-btn ${c === (filter || 'Alles') ? 'active' : ''}" onclick="renderProviders('${c === 'Alles' ? '' : c}')">${c}</button>`
  ).join("");
  gEl.innerHTML = list.map(p => {
    const full = Math.floor(p.rating);
    const half = p.rating % 1 >= 0.5;
    return `<div class="purchase-card" style="margin-bottom:10px;padding:14px">
      <div style="font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;color:var(--sage);margin-bottom:2px">${p.category}</div>
      <div class="purchase-card-name">${p.name}</div>
      <div style="font-size:12px;color:var(--text-muted);margin-bottom:10px"><span style="color:#d4a847">${'\\u2605'.repeat(full)}${half ? '\\u00BD' : ''}</span> ${p.city}</div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px">
        <a class="wa-link" href="https://wa.me/${p.phone}?text=Hallo ${p.name}, ik heb via HouseFix AI een klus en wil graag een offerte." target="_blank" style="display:flex;align-items:center;justify-content:center;gap:4px;padding:10px;border-radius:8px;font-size:12px;font-weight:700;text-decoration:none;background:#1F1E1C;color:#FFFFFF;border:1px solid rgba(255,255,255,0.1);letter-spacing:0.5px;transition:all 0.2s">\\u2728 WhatsApp</a>
        <button onclick="alert('Offerte aanvragen is binnenkort beschikbaar!')" style="display:flex;align-items:center;justify-content:center;gap:4px;padding:10px;border-radius:8px;font-size:12px;font-weight:700;border:1px solid var(--border-light);background:var(--bg-card);color:var(--text-secondary);cursor:pointer;transition:all 0.2s">\\uD83D\\uDCCB Offerte</button>
      </div>
    </div>`;
  }).join("");
}"""
    html = html[:rp_start] + new_rp + html[rp_end:]

with open(path, "w", encoding="utf-8") as f:
    f.write(html)

print("done")