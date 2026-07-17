#!/usr/bin/env python3
"""UX fixes: neutral buttons + smart back navigation + glow."""
p = "/home/team/shared/backend/templates/index.html"
with open(p, "r") as f:
    s = f.read()

# 1. Make both buttons equally neutral (transparent background)
old_btns = 'html += `<div style="margin-top:16px;display:grid;grid-template-columns:1fr 1fr;gap:8px">`;\n  html += `<button class="cta-btn" onclick="showDiyRoute(currentResult)" style="padding:12px;font-size:14px;font-weight:600">Zelf doen</button>`;\n  html += `<button class="cta-btn" onclick="showProRoute(currentResult)" style="padding:12px;font-size:14px;font-weight:600;background:transparent;color:var(--text-primary);border:1.5px solid var(--border-light)">Laten doen</button>`;'
neutr = 'padding:12px;font-size:14px;font-weight:600;background:transparent;color:var(--text-primary);border:1.5px solid var(--border-light)'
new_btns = f'html += `<div style="margin-top:16px;display:grid;grid-template-columns:1fr 1fr;gap:8px">`;\n  html += `<button class="cta-btn" onclick="showDiyRoute(currentResult)" style="{neutr}">Zelf doen</button>`;\n  html += `<button class="cta-btn" onclick="showProRoute(currentResult)" style="{neutr}">Laten doen</button>`;'
s = s.replace(old_btns, new_btns)

# 2. Add currentStep variable
s = s.replace('function goHome() {', 'let currentStep = "home";\nfunction goHome() {')

# 3. Update goHome to reset step
s = s.replace('function goHome() {\n  currentResult = null;\n  currentResultImage = "";', 'function goHome() {\n  currentStep = "home";\n  currentResult = null;\n  currentResultImage = "";')

# 4. Change backBtn onclick from goHome to goBack
s = s.replace('onclick="goHome()" aria-label="Terug">', 'onclick="goBack()" aria-label="Terug">')

# 5. Add goBack function and glow CSS
s = s.replace('function startAnalysis() {', 'function goBack() {\n  if (currentStep === "diy" || currentStep === "pro") {\n    showResults(currentResult);\n  } else {\n    goHome();\n  }\n}\nfunction startAnalysis() {')

# 6. Add glow to backBtn CSS (find existing .header-btn styles)
old_header_btn = '.header-btn { background: none; border: none; color: var(--text-secondary); font-size: 18px; cursor: pointer; padding: 4px 8px; display: flex; align-items: center; gap: 6px; transition: all 0.2s; width: 36px; justify-content: center; }'
new_header_btn = '.header-btn { background: none; border: none; color: var(--text-secondary); font-size: 18px; cursor: pointer; padding: 4px 8px; display: flex; align-items: center; gap: 6px; transition: all 0.2s; width: 36px; justify-content: center; }\n          #backBtn:hover { color: var(--terracotta); text-shadow: 0 0 8px rgba(196,98,74,0.4); }'
s = s.replace(old_header_btn, new_header_btn)

# 7. Set currentStep in showResults
s = s.replace('  resultContent.innerHTML = html;\n  saveBtn.style.display = "none";\n}\nfunction showDiyRoute(r) {', '  resultContent.innerHTML = html;\n  saveBtn.style.display = "none";\n  currentStep = "diagnose";\n}\nfunction showDiyRoute(r) {')

# 8. Set currentStep in showDiyRoute
old_diy_end = '  resultContent.innerHTML = html;\n  saveBtn.style.display = "none";\n}\n'
new_diy_end = '  resultContent.innerHTML = html;\n  saveBtn.style.display = "none";\n  currentStep = "diy";\n}\n'
s1 = s.split('function showDiyRoute')
parts = s1[1].split('function showProRoute')
parts[0] = parts[0].replace(old_diy_end, new_diy_end)
s1[1] = 'function showDiyRoute' + parts[0] + 'function showProRoute' + parts[1]
s = s1[0] + s1[1]

# 9. Set currentStep in showProRoute
old_pro_end = '  resultContent.innerHTML = html;\n  saveBtn.style.display = "none";\n  if (providers && providers.length) renderProviders();\n}\n'
new_pro_end = '  resultContent.innerHTML = html;\n  saveBtn.style.display = "none";\n  currentStep = "pro";\n  if (providers && providers.length) renderProviders();\n}\n'
s1 = s.split('function showProRoute')
parts = s1[1].split('function renderProviders')
parts[0] = parts[0].replace(old_pro_end, new_pro_end)
s1[1] = 'function showProRoute' + parts[0] + 'function renderProviders' + parts[1]
s = s1[0] + s1[1]

with open(p, "w") as f:
    f.write(s)
print("done")