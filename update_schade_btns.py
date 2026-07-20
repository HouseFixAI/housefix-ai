#!/usr/bin/env python3
"""Update Schade Expert knoppen: emoji weg, subtiele kleur, toggle, geen terug-link."""
import subprocess

p = "/home/team/shared/backend/templates/index.html"
with open(p, "r") as f:
    s = f.read()

# ── 1. Vervang showDamageExpert knoppen sectie ──
old_btns = """      // Twee contextuele knoppen: Details en Advies
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
      html += '</div></div>';"""

new_btns = """      // Twee contextuele knoppen: Details en Advies (toggle, geen emoji)
      html += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:12px">';
      html += '<div id="damDetBtn" onclick="toggleDamageSection(\\'details\\')" style="cursor:pointer;padding:12px 14px;border-radius:var(--radius-sm);background:var(--bg-card);border:1px solid var(--border-light);text-align:center;transition:all 0.2s">';
      html += '<div style="font-size:12px;font-weight:700;color:var(--text-secondary);letter-spacing:0.3px">Details</div>';
      html += '<div style="font-size:10px;color:var(--text-muted);margin-top:2px">Oorzaak & risico</div>';
      html += '</div>';
      html += '<div id="damAdvBtn" onclick="toggleDamageSection(\\'advice\\')" style="cursor:pointer;padding:12px 14px;border-radius:var(--radius-sm);background:var(--bg-card);border:1px solid var(--border-light);text-align:center;transition:all 0.2s">';
      html += '<div style="font-size:12px;font-weight:700;color:var(--text-secondary);letter-spacing:0.3px">Advies</div>';
      html += '<div style="font-size:10px;color:var(--text-muted);margin-top:2px">Wat nu te doen</div>';
      html += '</div></div>';"""

s = s.replace(old_btns, new_btns)

# ── 2. Vervang showDamageDetails (toggle-aware, geen terug-link) ──
old_det = """    function showDamageDetails(r) {
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
        html += '<div style="font-size:13px;color:var(--text-secondary);line-height:1.6">'+ (r.description || "Geen verdere details beschikbaar voor deze schade.") +'</div>';
      }
      html += '</div></div>';
      html += '<div style="text-align:center;margin-bottom:8px"><button onclick="showDamageExpert(currentResult)" style="background:none;border:none;color:var(--text-muted);font-size:12px;cursor:pointer;padding:4px 12px">\\u2190 Terug naar diagnose</button></div>';
      dd.innerHTML = html;
    }"""

new_det = """    function showDamageDetails(r) {
      const dd = document.getElementById("damDetail");
      let html = '';
      html += '<div style="margin-bottom:12px;border-radius:var(--radius-sm);border:1px solid var(--border-light);background:var(--bg-card);overflow:hidden">';
      html += '<div style="padding:10px 14px;background:var(--bg-secondary);font-size:13px;font-weight:700;color:var(--text-primary);letter-spacing:0.3px">Details & oorzaak</div>';
      html += '<div style="padding:14px">';
      if (r.cause) {
        html += '<div style="font-size:13px;color:var(--text-secondary);line-height:1.6;margin-bottom:10px">'+r.cause+'</div>';
      }
      if (r.risk) {
        html += '<div style="padding:8px 10px;border-radius:8px;background:rgba(196,98,74,0.06);border:1px solid rgba(196,98,74,0.12);font-size:12px;color:var(--terracotta);line-height:1.5">\\u26a0\\ufe0f '+r.risk+'</div>';
      }
      if (!r.cause && !r.risk) {
        html += '<div style="font-size:13px;color:var(--text-secondary);line-height:1.6">'+ (r.description || "Geen verdere details beschikbaar voor deze schade.") +'</div>';
      }
      html += '</div></div>';
      dd.innerHTML = html;
    }"""

s = s.replace(old_det, new_det)

# ── 3. Vervang showDamageAdvice (toggle-aware, geen terug-link) ──
old_adv = """    function showDamageAdvice(r) {
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
        html += '<div style="font-size:13px;color:var(--text-secondary);line-height:1.6">'+ (r.description || "Geen specifiek advies beschikbaar. Gebruik de knoppen hieronder om reparatie-opties te bekijken.") +'</div>';
      }
      html += '</div></div>';
      html += '<div style="text-align:center;margin-bottom:8px"><button onclick="showDamageExpert(currentResult)" style="background:none;border:none;color:var(--text-muted);font-size:12px;cursor:pointer;padding:4px 12px">\\u2190 Terug naar diagnose</button></div>';
      dd.innerHTML = html;
    }"""

new_adv = """    function showDamageAdvice(r) {
      const dd = document.getElementById("damDetail");
      let html = '';
      const urgent = r.urgency || "medium";
      const urgencyMap = { high: { label: "Direct actie nodig", color: "var(--terracotta)", icon: "\\u26a0\\ufe0f" }, medium: { label: "Houd in de gaten", color: "var(--sage)", icon: "\\ud83d\\udcc5" }, low: { label: "Kan wachten", color: "var(--text-muted)", icon: "\\ud83d\\ude34" } };
      const u = urgencyMap[urgent] || urgencyMap.medium;
      html += '<div style="margin-bottom:12px;border-radius:var(--radius-sm);border:1px solid var(--border-light);background:var(--bg-card);overflow:hidden">';
      html += '<div style="padding:10px 14px;background:var(--bg-secondary);font-size:13px;font-weight:700;color:var(--text-primary);letter-spacing:0.3px">Advies</div>';
      html += '<div style="padding:14px">';
      html += '<div style="display:inline-block;padding:4px 10px;border-radius:6px;font-size:11px;font-weight:700;color:#fff;background:'+u.color+';margin-bottom:10px">'+u.icon+' '+u.label+'</div>';
      if (r.advice) {
        html += '<div style="font-size:13px;color:var(--text-secondary);line-height:1.6;margin-bottom:10px">'+r.advice+'</div>';
      }
      if (!r.advice && !r.cause && !r.risk) {
        html += '<div style="font-size:13px;color:var(--text-secondary);line-height:1.6">'+ (r.description || "Geen specifiek advies beschikbaar. Gebruik de knoppen hieronder om reparatie-opties te bekijken.") +'</div>';
      }
      html += '</div></div>';
      dd.innerHTML = html;
    }"""

s = s.replace(old_adv, new_adv)

# ── 4. Voeg toggleDamageSection functie toe vóór showDamageDetails ──
toggle_func = """
    var _damageSectionOpen = null;
    function toggleDamageSection(section) {
      if (_damageSectionOpen === section) {
        document.getElementById("damDetail").innerHTML = '';
        document.getElementById("damDetBtn").style.background = "var(--bg-card)";
        document.getElementById("damDetBtn").style.borderColor = "var(--border-light)";
        document.getElementById("damAdvBtn").style.background = "var(--bg-card)";
        document.getElementById("damAdvBtn").style.borderColor = "var(--border-light)";
        _damageSectionOpen = null;
        return;
      }
      _damageSectionOpen = section;
      if (section === 'details') {
        document.getElementById("damDetBtn").style.background = "rgba(138,155,122,0.08)";
        document.getElementById("damDetBtn").style.borderColor = "rgba(138,155,122,0.25)";
        document.getElementById("damAdvBtn").style.background = "var(--bg-card)";
        document.getElementById("damAdvBtn").style.borderColor = "var(--border-light)";
        showDamageDetails(currentResult);
      } else {
        document.getElementById("damAdvBtn").style.background = "rgba(196,98,74,0.08)";
        document.getElementById("damAdvBtn").style.borderColor = "rgba(196,98,74,0.25)";
        document.getElementById("damDetBtn").style.background = "var(--bg-card)";
        document.getElementById("damDetBtn").style.borderColor = "var(--border-light)";
        showDamageAdvice(currentResult);
      }
    }
"""

# Insert toggle function before showDamageDetails
old_marker = "    function showDamageDetails(r) {"
s = s.replace(old_marker, toggle_func + "\n" + old_marker, 1)

with open(p, "w") as f:
    f.write(s)
print("Schade Expert knoppen geüpdatet: emoji weg, subtiele kleur, toggle, geen terug-link")

# JS check
r = subprocess.run(["node", "-e", """
const fs=require('fs');
const p=require('path');
const s=fs.readFileSync(p.join(process.env.HOME || '/home/agent-lead','/home/team/shared/backend/templates/index.html'),'utf8');
const m=s.match(/<script>([\\s\\S]*?)<\\/script>/);
try{new Function(m[1]);console.log('JS_OK')}catch(e){console.log('JS Error: '+e.message)}
"""], capture_output=True, text=True, cwd="/home/team/shared")
print(r.stdout.strip())