#!/usr/bin/env python3
"""Rewrite showDamageExpert: diagnose-first, Details/Advies knoppen, premium flow."""
import subprocess

p = "/home/team/shared/backend/templates/index.html"
with open(p, "r") as f:
    s = f.read()

new_func = """    function showDamageExpert(r) {
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
      // Foto centraal
      html += '<div style="border-radius:var(--radius-sm);overflow:hidden;position:relative;margin-bottom:12px;background:var(--border-light);min-height:180px;display:flex;align-items:center;justify-content:center">';
      if (currentResultImage) {
        html += '<img src="'+currentResultImage+'" style="width:100%;display:block;max-height:220px;object-fit:cover" onerror="this.style.display=\\'none\\'" />';
      }
      html += '<div style="position:absolute;bottom:0;left:0;right:0;padding:14px 16px;background:linear-gradient(transparent,rgba(0,0,0,0.7))">';
      html += '<div style="font-size:17px;font-weight:700;color:#fff">'+it+'</div>';
      html += '<span class="badge '+b.c+'" style="margin-top:3px">'+b.l+' vertrouwen</span></div></div>';
      // Diagnose compact
      html += '<div class="advice-section" style="padding-top:0"><div style="font-size:14px;color:var(--text-secondary);line-height:1.6;margin-bottom:12px">'+desc+'</div>';
      // Veiligheid
      if (r.warning) {
        html += '<div style="padding:10px 14px;border-radius:10px;background:rgba(196,98,74,0.06);border:1px solid rgba(196,98,74,0.12);font-size:13px;color:var(--terracotta);line-height:1.5;margin-bottom:12px">\\u26a0\\ufe0f '+r.warning+'</div>';
      }
      // Twee contextuele knoppen: Details en Advies
      html += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:12px">';
      html += '<div id="damDetBtn" onclick="showDamageDetails(currentResult)" style="cursor:pointer;padding:14px;border-radius:var(--radius-sm);background:var(--bg-card);border:1px solid var(--border-light);text-align:center;transition:all 0.2s">';
      html += '<div style="font-size:20px;margin-bottom:2px">\\ud83d\\udd0d</div>';
      html += '<div style="font-size:11px;font-weight:700;color:var(--text-primary);letter-spacing:0.3px">Details</div>';
      html += '<div style="font-size:10px;color:var(--text-muted);margin-top:1px">Oorzaak & risico</div>';
      html += '</div>';
      html += '<div id="damAdvBtn" onclick="showDamageAdvice(currentResult)" style="cursor:pointer;padding:14px;border-radius:var(--radius-sm);background:var(--bg-card);border:1px solid var(--border-light);text-align:center;transition:all 0.2s">';
      html += '<div style="font-size:20px;margin-bottom:2px">\\ud83d\\udccb</div>';
      html += '<div style="font-size:11px;font-weight:700;color:var(--text-primary);letter-spacing:0.3px">Advies</div>';
      html += '<div style="font-size:10px;color:var(--text-muted);margin-top:1px">Wat nu te doen</div>';
      html += '</div></div>';
      // Container voor verdieping
      html += '<div id="damDetail"></div>';
      // Navigatie naar reparatie en kosten (blijft)
      html += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">';
      html += '<button class="cta-btn" onclick="showRepairExpert(currentResult)" style="padding:12px;font-size:13px;font-weight:600;background:transparent;color:var(--text-primary);border:1.5px solid var(--border-light)">\\ud83d\\udee0\\ufe0f Repareren</button>';
      html += '<button class="cta-btn" onclick="showCostEstimate(currentResult)" style="padding:12px;font-size:13px;font-weight:600;background:transparent;color:var(--text-primary);border:1.5px solid var(--border-light)">\\ud83d\\udcb0 Kosten</button>';
      html += '</div></div>';
      html += '<div style="height:40px"></div>';
      rc.innerHTML = html;
      saveBtn.style.display = "none";
      currentStep = "diagnose";
    }

    function showDamageDetails(r) {
      const dd = document.getElementById("damDetail");
      let html = '';
      html += '<div style="margin-bottom:12px;border-radius:var(--radius-sm);border:1px solid var(--border-light);background:var(--bg-card);overflow:hidden">';
      html += '<div style="padding:10px 14px;background:var(--bg-secondary);font-size:13px;font-weight:700;color:var(--text-primary);letter-spacing:0.3px">\\ud83d\\udd0d Details & oorzaak</div>';
      html += '<div style="padding:14px">';
      // Oorzaak
      if (r.cause) {
        html += '<div style="font-size:13px;color:var(--text-secondary);line-height:1.6;margin-bottom:10px">'+r.cause+'</div>';
      }
      // Risico/verergering
      if (r.risk) {
        html += '<div style="padding:8px 10px;border-radius:8px;background:rgba(196,98,74,0.06);border:1px solid rgba(196,98,74,0.12);font-size:12px;color:var(--terracotta);line-height:1.5">\\u26a0\\ufe0f '+r.risk+'</div>';
      }
      if (!r.cause && !r.risk) {
        html += '<div style="font-size:13px;color:var(--text-muted);text-align:center;padding:8px 0">Geen verdere details beschikbaar voor deze schade.</div>';
      }
      html += '</div></div>';
      html += '<div style="text-align:center;margin-bottom:8px"><button onclick="showDamageExpert(currentResult)" style="background:none;border:none;color:var(--text-muted);font-size:12px;cursor:pointer;padding:4px 12px">\\u2190 Terug naar diagnose</button></div>';
      dd.innerHTML = html;
    }

    function showDamageAdvice(r) {
      const dd = document.getElementById("damDetail");
      let html = '';
      // Bepaal urgentie
      const urgent = r.urgency || "medium";
      const urgencyMap = { high: { label: "Direct actie nodig", color: "var(--terracotta)", icon: "\\u26a0\\ufe0f" }, medium: { label: "Houd in de gaten", color: "var(--sage)", icon: "\\ud83d\\udcc5" }, low: { label: "Kan wachten", color: "var(--text-muted)", icon: "\\ud83d\\ude34" } };
      const u = urgencyMap[urgent] || urgencyMap.medium;
      html += '<div style="margin-bottom:12px;border-radius:var(--radius-sm);border:1px solid var(--border-light);background:var(--bg-card);overflow:hidden">';
      html += '<div style="padding:10px 14px;background:var(--bg-secondary);font-size:13px;font-weight:700;color:var(--text-primary);letter-spacing:0.3px">\\ud83d\\udccb Advies</div>';
      html += '<div style="padding:14px">';
      // Urgentie badge
      html += '<div style="display:inline-block;padding:4px 10px;border-radius:6px;font-size:11px;font-weight:700;color:#fff;background:'+u.color+';margin-bottom:10px">'+u.icon+' '+u.label+'</div>';
      // Advies tekst
      if (r.advice) {
        html += '<div style="font-size:13px;color:var(--text-secondary);line-height:1.6;margin-bottom:10px">'+r.advice+'</div>';
      }
      if (!r.advice && !r.cause && !r.risk) {
        html += '<div style="font-size:13px;color:var(--text-muted);text-align:center;padding:8px 0">Geen specifiek advies beschikbaar. Gebruik de knoppen hieronder om reparatie-opties te bekijken.</div>';
      }
      html += '</div></div>';
      html += '<div style="text-align:center;margin-bottom:8px"><button onclick="showDamageExpert(currentResult)" style="background:none;border:none;color:var(--text-muted);font-size:12px;cursor:pointer;padding:4px 12px">\\u2190 Terug naar diagnose</button></div>';
      dd.innerHTML = html;
    }"""

# Find showDamageExpert
old_start = "    function showDamageExpert(r) {"
# Next function after it is showDiyRoute (0 indent)
next_func = "    function showRepairExpert"
idx_start = s.find(old_start)
idx_end = s.find(next_func, idx_start)
if idx_start < 0 or idx_end < 0:
    print("ERROR: boundaries not found"); exit(1)

s = s[:idx_start] + new_func + "\n\n" + s[idx_end:]

with open(p, "w") as f:
    f.write(s)
print("showDamageExpert + showDamageDetails + showDamageAdvice replaced")

r = subprocess.run(["node", "-e", """
const fs=require('fs');
const s=fs.readFileSync('backend/templates/index.html','utf8');
const m=s.match(/<script>([\\s\\S]*?)<\\/script>/);
try{new Function(m[1]);console.log('JS_OK')}catch(e){console.log('JS Error: '+e.message)}
"""], capture_output=True, text=True, cwd="/home/team/shared")
print(r.stdout.strip())