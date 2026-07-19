#!/usr/bin/env python3
"""Complete rebuild of the four specialists - single script, atomic execution."""
import subprocess, os

# Restore clean file first
subprocess.run(["git", "-C", "/home/team/shared", "checkout", "--", "backend/templates/index.html"], check=True)

p = "/home/team/shared/backend/templates/index.html"
with open(p, "r") as f:
    s = f.read()

# ── 1. Carousel damage items ──
old_damage = """      damage: [
        {bg:"url(https://images.unsplash.com/photo-1504307651254-35680f356dfd?w=800&h=480&fit=crop&fm=webp&q=85)", t:"Analyseer Schade", a:"openCamera()"},
        {bg:"url(https://images.unsplash.com/photo-1581578731548-c64695cc6952?w=800&h=480&fit=crop&fm=webp&q=85)", t:"Kosten Schatting", a:"openCameraForIntent('cost')"},
        {bg:"url(https://images.unsplash.com/photo-1581539250439-c96689b516dd?w=800&h=480&fit=crop&fm=webp&q=85)", t:"Reparatieplan", a:"openCamera()"},
        {bg:"url(https://images.unsplash.com/photo-1504148455328-c376907d081c?w=800&h=480&fit=crop&fm=webp&q=85)", t:"Materialenlijst", a:"openCamera()"}
      ],"""
new_damage = """      damage: [
        {bg:"url(https://images.unsplash.com/photo-1504307651254-35680f356dfd?w=800&h=480&fit=crop&fm=webp&q=85)", t:"\\ud83d\\udd0d Schade Expert", a:"openCameraForIntent('damage_expert')"},
        {bg:"url(https://images.unsplash.com/photo-1581578731548-c64695cc6952?w=800&h=480&fit=crop&fm=webp&q=85)", t:"\\ud83d\\udcb0 Kosten Expert", a:"openCameraForIntent('cost_expert')"},
        {bg:"url(https://images.unsplash.com/photo-1581539250439-c96689b516dd?w=800&h=480&fit=crop&fm=webp&q=85)", t:"\\ud83d\\udee0\\ufe0f Reparatie Expert", a:"openCameraForIntent('repair_expert')"}
      ],"""
s = s.replace(old_damage, new_damage)

# ── 2. Carousel inspiration items ──
old_inspo = """      inspiration: [
        {bg:"url(https://images.unsplash.com/photo-1513519245088-0e12902e35ca?w=800&h=480&fit=crop&fm=webp&q=85)", t:"Scan voor Kleurenpalet", a:"openCameraForIntent('identify')"},
        {bg:"url(https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=800&h=480&fit=crop&fm=webp&q=85)", t:"Vind dit Meubel", a:"openCameraForIntent('find_item')"},
        {bg:"url(https://images.unsplash.com/photo-1616486338812-3dadae4b4ace?w=800&h=480&fit=crop&fm=webp&q=85)", t:"Stijl mijn Kamer", a:"openCameraForIntent('style_room')"},
        {bg:"url(https://images.unsplash.com/photo-1513694203232-719a280e022f?w=800&h=480&fit=crop&fm=webp&q=85)", t:"Raamdecoratie", a:"openCamera()"}
      ]"""
new_inspo = """      inspiration: [
        {bg:"url(https://images.unsplash.com/photo-1513519245088-0e12902e35ca?w=800&h=480&fit=crop&fm=webp&q=85)", t:"\\ud83c\\udfe1 Wooncoach", a:"openCameraForIntent('interior_coach')"},
        {bg:"url(https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=800&h=480&fit=crop&fm=webp&q=85)", t:"\\ud83d\\udccb Shopadvies", a:"openCameraForIntent('identify')"},
        {bg:"url(https://images.unsplash.com/photo-1616486338812-3dadae4b4ace?w=800&h=480&fit=crop&fm=webp&q=85)", t:"Stijl mijn Kamer", a:"openCameraForIntent('style_room')"},
        {bg:"url(https://images.unsplash.com/photo-1513694203232-719a280e022f?w=800&h=480&fit=crop&fm=webp&q=85)", t:"Raamdecoratie", a:"openCamera()"}
      ]"""
s = s.replace(old_inspo, new_inspo)

# ── 3. RenderResults switch ──
old_switch = """        switch (intent) {
          case "purchase":
            renderColorPalette(data);
            break;
          case "find_item":
            renderFindItem(data);
            break;
          case "style_room":
            renderStyleRoom(data);
            break;
          case "style":
            showInspirationAdvice(data);
            break;
          case "cost":
            showCostEstimate(data);
            break;
          default:
            showResults(data);
        }"""
new_switch = """        switch (intent) {
          case "damage_expert":
            showDamageExpert(data);
            break;
          case "repair_expert":
            showRepairExpert(data);
            break;
          case "cost_expert":
            showCostEstimate(data);
            break;
          case "interior_coach":
            showInteriorCoach(data);
            break;
          case "purchase":
            renderColorPalette(data);
            break;
          case "find_item":
            renderFindItem(data);
            break;
          case "style_room":
            renderStyleRoom(data);
            break;
          case "style":
            showInspirationAdvice(data);
            break;
          default:
            showResults(data);
        }"""
s = s.replace(old_switch, new_switch)

# ── 4. Insert showDamageExpert and showRepairExpert function definitions ──
# Place them after showResults (which ends with the diagnose section + } }) but BEFORE showDiyRoute
# showResults is the DEFAULT handler in the switch. It's defined as a top-level function.
# We insert after the showResults function body ends.

# The showResults function ends with pattern:
#   currentStep = "diagnose";\n  }\n
# This is followed by functions like renderColorPalette, showDiyRoute, etc.

# Let's insert our new functions right before showDiyRoute
damage_expert_func = """
    function showDamageExpert(r) {
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
      html += '<div style="border-radius:var(--radius-sm);overflow:hidden;position:relative;margin-bottom:12px;background:var(--border-light);min-height:180px;display:flex;align-items:center;justify-content:center">';
      if (currentResultImage) {
        html += '<img src="'+currentResultImage+'" style="width:100%;display:block;max-height:220px;object-fit:cover" onerror="this.style.display=\\'none\\'" />';
      }
      html += '<div style="position:absolute;bottom:0;left:0;right:0;padding:14px 16px;background:linear-gradient(transparent,rgba(0,0,0,0.7))">';
      html += '<div style="font-size:17px;font-weight:700;color:#fff">'+it+'</div>';
      html += '<span class="badge '+b.c+'" style="margin-top:3px">'+b.l+' vertrouwen</span></div></div>';
      html += '<div class="advice-section" style="padding-top:0"><div style="font-size:14px;color:var(--text-secondary);line-height:1.6;margin-bottom:8px">'+desc+'</div>';
      if (r.warning) {
        html += '<div style="padding:10px 14px;border-radius:10px;background:rgba(196,98,74,0.06);border:1px solid rgba(196,98,74,0.12);font-size:13px;color:var(--terracotta);line-height:1.5;margin-bottom:12px">\\u26a0\\ufe0f '+r.warning+'</div>';
      }
      html += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:4px">';
      html += '<button class="cta-btn" onclick="showRepairExpert(currentResult)" style="padding:12px;font-size:13px;font-weight:600;background:transparent;color:var(--text-primary);border:1.5px solid var(--border-light)">\\ud83d\\udee0\\ufe0f Repareren</button>';
      html += '<button class="cta-btn" onclick="showCostEstimate(currentResult)" style="padding:12px;font-size:13px;font-weight:600;background:transparent;color:var(--text-primary);border:1.5px solid var(--border-light)">\\ud83d\\udcb0 Kosten</button>';
      html += '</div></div>';
      html += '<div style="height:40px"></div>';
      rc.innerHTML = html;
      saveBtn.style.display = "none";
      currentStep = "diagnose";
    }

    function showRepairExpert(r) {
      currentResult = r;
      const snapEl = document.getElementById("snapshot");
      currentResultImage = snapEl.src || "";
      const saveBtn = document.getElementById("saveBtn");
      const rc = document.getElementById("resultContent");
      let html = "";
      if (r.is_fallback || r.no_damage || r.warning) { showResults(r); return; }
      const it = r.issue_type || "Reparatie";
      const desc = r.description || "";
      html += '<div class="advice-section"><div class="identify-head" style="font-size:20px;margin-bottom:2px">\\ud83d\\udee0\\ufe0f '+it+'</div>';
      html += '<div style="font-size:13px;color:var(--text-muted);margin-bottom:12px">'+desc+'</div>';
      if (r.steps && r.steps.length) {
        html += '<div class="advice-subhead" style="margin-top:4px">Stappenplan</div>';
        r.steps.forEach(function(s, i) {
          html += '<div class="step-item"><div class="step-num">'+(i+1)+'</div><div class="step-txt">'+s+'</div></div>';
        });
      }
      if (r.materials && r.materials.length) {
        html += '<div class="advice-subhead" style="margin-top:12px">Materialen</div><div class="advice-materials">';
        r.materials.forEach(function(m) { html += '<span class="advice-material">'+m+'</span>'; });
        html += '</div>';
        const gammaTips = (r.gamma_tips && r.gamma_tips.length) ? r.gamma_tips.join(", ") : r.materials.join(", ");
        html += '<div style="margin-top:8px"><a class="gamma-link" href="https://www.gamma.nl/zoeken?q='+encodeURIComponent(gammaTips)+'" target="_blank">Bestel bij Gamma</a></div>';
      }
      html += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:16px">';
      html += '<button class="cta-btn" onclick="showDamageExpert(currentResult)" style="padding:12px;font-size:13px;font-weight:600;background:transparent;color:var(--text-primary);border:1.5px solid var(--border-light)">\\ud83d\\udd0d Schade</button>';
      html += '<button class="cta-btn" onclick="showCostEstimate(currentResult)" style="padding:12px;font-size:13px;font-weight:600;background:transparent;color:var(--text-primary);border:1.5px solid var(--border-light)">\\ud83d\\udcb0 Kosten</button>';
      html += '</div>';
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
    }
"""

# Insert before showDiyRoute
target = "\nfunction showDiyRoute(r) {"
s = s.replace(target, damage_expert_func + "\nfunction showDiyRoute(r) {")

with open(p, "w") as f:
    f.write(s)
print("all changes applied")

# Validate JS syntax
import subprocess
r = subprocess.run(["node", "-e", """
const fs=require('fs');
const s=fs.readFileSync('backend/templates/index.html','utf8');
const m=s.match(/<script>([\\s\\S]*?)<\\/script>/);
try{new Function(m[1]);console.log('JS_OK')}catch(e){console.log('JS Error: '+e.message)}
"""], capture_output=True, text=True, cwd="/home/team/shared")
print(r.stdout.strip())
if r.stderr:
    print(r.stderr.strip())