#!/usr/bin/env python3
"""Premium visual upgrade for Klus Hulp results page."""
import subprocess

path = "/home/team/shared/backend/templates/index.html"
with open(path, "r", encoding="utf-8") as f:
    html = f.read()

# 1. Replace showResults function
start_marker = "function showResults(r) {"
start_idx = html.find(start_marker)
end_marker = "\nfunction toggleProviders()"
end_idx = html.find(end_marker, start_idx)

if start_idx < 0 or end_idx < 0:
    print("ERROR: markers not found")
    exit(1)

func_start = html.rfind("\n", 0, start_idx) + 1
func_end = end_idx

# Read new showResults
with open("/home/team/shared/new_showResults_v2.txt", "r", encoding="utf-8") as f:
    new_showResults = f.read()

print(f"Replacing showResults at {func_start}-{func_end}")
html = html[:func_start] + new_showResults + html[func_end:]

# 2. Replace renderProviders with premium version
old_renderProviders = """function renderProviders(filter) {
  const list = filter ? providers.filter(p => p.category === filter) : providers;
  const cats = ["Alles", ...new Set(providers.map(p => p.category))];
  document.getElementById("provFilters").innerHTML = cats.map(c =>
    `<button class="filter-btn ${c === (filter || 'Alles') ? 'active' : ''}" onclick="renderProviders('${c === 'Alles' ? '' : c}')">${c}</button>`
  ).join("");
  document.getElementById("provGrid").innerHTML = list.map(p => {
    const full = Math.floor(p.rating);
    const half = p.rating % 1 >= 0.5;
    return `<div class="prov-card">
      <div class="prov-cat">${p.category}</div>
      <div class="prov-name">${p.name}</div>
      <div class="prov-meta"><span class="prov-stars">${'★'.repeat(full)}${half ? '½' : ''}</span> ${p.city}</div>
      <div class="prov-actions">
        <a class="wa-link" href="https://wa.me/${p.phone}?text=Hallo ${p.name}, ik heb via HouseFix AI een klus en wil graag een offerte." target="_blank">💬 WhatsApp</a>
        <button class="quote-btn-sm" onclick="alert('Offerte aanvragen is binnenkort beschikbaar!')">📋 Offerte</button>
      </div>
    </div>`;
  }).join("");
}"""

new_renderProviders = """function renderProviders(filter) {
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
      <div class="prov-cat" style="font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;color:var(--sage);margin-bottom:2px">${p.category}</div>
      <div class="purchase-card-name">${p.name}</div>
      <div style="font-size:12px;color:var(--text-muted);margin-bottom:10px"><span style="color:#d4a847">${'★'.repeat(full)}${half ? '½' : ''}</span> ${p.city}</div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px">
        <a class="wa-link" href="https://wa.me/${p.phone}?text=Hallo ${p.name}, ik heb via HouseFix AI een klus en wil graag een offerte." target="_blank" style="display:flex;align-items:center;justify-content:center;gap:4px;padding:10px;border-radius:8px;font-size:12px;font-weight:700;text-decoration:none;background:#1F1E1C;color:#FFFFFF;border:1px solid rgba(255,255,255,0.1);letter-spacing:0.5px;transition:all 0.2s">💬 WhatsApp</a>
        <button class="quote-btn-sm" onclick="alert('Offerte aanvragen is binnenkort beschikbaar!')" style="display:flex;align-items:center;justify-content:center;gap:4px;padding:10px;border-radius:8px;font-size:12px;font-weight:700;border:1px solid var(--border-light);background:var(--bg-card);color:var(--text-secondary);cursor:pointer;transition:all 0.2s">📋 Offerte</button>
      </div>
    </div>`;
  }).join("");
}"""

if old_renderProviders in html:
    html = html.replace(old_renderProviders, new_renderProviders, 1)
    print("renderProviders replaced")
else:
    print("WARNING: could not find old renderProviders")

# 3. Remove toggleProviders function (no longer needed)
old_toggle = "function toggleProviders() {\n  const body = document.getElementById(\"accordionBody\");\n  const arrow = document.getElementById(\"accordionArrow\");\n  body.classList.toggle(\"open\");\n  arrow.classList.toggle(\"open\");\n}\n\n"
if old_toggle in html:
    html = html.replace(old_toggle, "", 1)
    print("toggleProviders removed")
else:
    print("WARNING: could not find toggleProviders")

# 4. Update goHome to remove accordion reset
old_goHome_acc = "  // Reset accordion\n  document.getElementById(\"accordionBody\").classList.remove(\"open\");\n  document.getElementById(\"accordionArrow\").classList.remove(\"open\");\n}"
new_goHome_acc = "}"
if old_goHome_acc in html:
    html = html.replace(old_goHome_acc, new_goHome_acc, 1)
    print("goHome accordion reset removed")
else:
    print("WARNING: could not find goHome accordion reset")

with open(path, "w", encoding="utf-8") as f:
    f.write(html)

# Verify JS syntax
result = subprocess.run(
    ["node", "-e",
     "try{const fs=require('fs');const s=fs.readFileSync('" + path + "','utf8');"
     "const m=s.match(/<script>([\\s\\S]*?)<\\/script>/);"
     "if(!m){console.log('NO_MATCH');process.exit(1)}"
     "new Function(m[1]);console.log('JS_OK')"
     "}catch(e){console.log('JS_ERROR:',e.message);process.exit(1)}"],
    capture_output=True, text=True, shell=True, timeout=10
)
print(result.stdout.strip())
if result.returncode != 0:
    print("STDERR:", result.stderr.strip())
    exit(1)