#!/usr/bin/env python3
"""Build the four AI specialists architecture."""
p = "/home/team/shared/backend/templates/index.html"
with open(p, "r") as f:
    s = f.read()

# ── STEP 1: Update carousel damage items to the three experts ──
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

# ── STEP 2: Update inspiration carousel to Wooncoach ──
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

# ── STEP 3: Update renderResults switch ──
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

# ── STEP 4: Add showDamageExpert function ──
# Place it after showResults and before showDiyRoute
old_after_diy = "}\nfunction showDiyRoute(r) {"
new_before_diy = """}
function showDamageExpert(r) {
  // 🔍 Schade Expert: foto-centrisch, diagnose + ernst, minimale actie
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
  const b = { high:{c:"badge-high",l:"Hoog"}, medium:{c:"badge-medium",l:"Gemiddeld"}, low:{c:"badge-low",l:"Laag"} }[conf] || b.medium;
  // Foto centraal
  html += '<div style="margin-bottom:12px;border-radius:var(--radius-sm);overflow:hidden;position:relative">';
  html += '<img src="'+currentResultImage+'" style="width:100%;display:block;max-height:260px;object-fit:cover" onerror="this.style.display=\\'none\\'" />';
  html += '<div style="position:absolute;bottom:0;left:0;right:0;padding:16px;background:linear-gradient(transparent,rgba(0,0,0,0.7))"><div style="font-size:18px;font-weight:700;color:#fff">'+it+'</div><span class="badge '+b.c+'" style="margin-top:4px;display:inline-block">'+b.l+' vertrouwen</span></div></div>';
  // Diagnose compact
  html += '<div class="advice-section" style="padding-top:4px"><div style="font-size:14px;color:var(--text-secondary);line-height:1.6">'+desc+'</div></div>';
  // Veiligheid als relevant
  if (r.warning) {
    html += '<div style="padding:12px 16px;border-radius:12px;background:rgba(196,98,74,0.06);border:1px solid rgba(196,98,74,0.12);font-size:14px;color:var(--terracotta);line-height:1.5;margin:12px 0">\\u26a0\\ufe0f '+r.warning+'</div>';
  }
  // Secundaire navigatie - compacte knoppen naar andere experts
  html += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:16px">';
  html += '<button class="cta-btn" onclick="showRepairExpert(currentResult)" style="padding:12px;font-size:13px;font-weight:600;background:transparent;color:var(--text-primary);border:1.5px solid var(--border-light)">\\ud83d\\udee0\\ufe0f Repareren</button>';
  html += '<button class="cta-btn" onclick="showCostEstimate(currentResult)" style="padding:12px;font-size:13px;font-weight:600;background:transparent;color:var(--text-primary);border:1.5px solid var(--border-light)">\\ud83d\\udcb0 Kosten</button>';
  html += '</div>';
  html += '<div style="height:40px"></div>';
  rc.innerHTML = html;
  saveBtn.style.display = "none";
  currentStep = "diagnose";
}
function showDiRoute"""
# Fix: need to match exact text
old_diy_func = "}\nfunction showDiyRoute(r) {"
new_with_damage = """}
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
  // Foto centraal
  html += '<div class="advice-section" style="padding:0;overflow:hidden;border-radius:var(--radius-sm);position:relative;margin-bottom:12px">';
  html += '<div style="width:100%;height:200px;background:var(--border-light);display:flex;align-items:center;justify-content:center;font-size:48px;color:var(--text-muted)">\\ud83d\\udcf7</div>';
  html += '<div style="position:absolute;bottom:0;left:0;right:0;padding:16px;background:linear-gradient(transparent,rgba(0,0,0,0.7))"><div style="font-size:18px;font-weight:700;color:#fff">'+it+'</div></div></div>';
  html += '<div class="advice-section" style="padding-top:0"><div style="font-size:14px;color:var(--text-secondary);line-height:1.6;margin-bottom:12px">'+desc+'</div>';
  // Navigatie naar andere experts
  html += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">';
  html += '<button class="cta-btn" onclick="showRepairExpert(currentResult)" style="padding:12px;font-size:13px;font-weight:600;background:transparent;color:var(--text-primary);border:1.5px solid var(--border-light)">\\ud83d\\udee0\\ufe0f Repareren</button>';
  html += '<button class="cta-btn" onclick="showCostEstimate(currentResult)" style="padding:12px;font-size:13px;font-weight:600;background:transparent;color:var(--text-primary);border:1.5px solid var(--border-light)">\\ud83d\\udcb0 Kosten</button>';
  html += '</div></div>';
  html += '<div style="height:40px"></div>';
  rc.innerHTML = html;
  saveBtn.style.display = "none";
  currentStep = "diagnose";
}
function showDiyRoute"""
# Find the last } before showDiyRoute
import re
# Find the exact boundary
idx_diy = s.find("}\nfunction showDiyRoute(r)")
if idx_diy > 0:
    s = s[:idx_diy+1] + new_with_damage.split("}\nfunction showDiyRoute")[0] + s[idx_diy:]

with open(p, "w") as f:
    f.write(s)
print("phase1 done")