#!/usr/bin/env python3
"""Fix diagnose buttons: no emoji, side by side, compact. Remove extra back buttons."""
p = "/home/team/shared/backend/templates/index.html"
with open(p, "rb") as f:
    data = f.read()
text = data.decode("utf-8", errors="surrogateescape")

# Replace the diagnose buttons block
# Match emoji \uD83D\uDEE0\uFE0F and \uD83D\uDC77 as literal text in the file
old_btns = 'html += `<div style="margin-top:20px;display:flex;flex-direction:column;gap:10px">`;\n  html += `<button class="cta-btn" onclick="showDiyRoute(currentResult)" style="padding:16px;font-size:16px">\\uD83D\\uDEE0\\uFE0F  Zelf doen</button>`;\n  html += `<button class="cta-btn" onclick="showProRoute(currentResult)" style="padding:16px;font-size:16px;background:transparent;color:var(--text-primary);border:1.5px solid var(--border-light)">\\uD83D\\uDC77  Laten doen</button>`;'
new_btns = 'html += `<div style="margin-top:16px;display:grid;grid-template-columns:1fr 1fr;gap:8px">`;\n  html += `<button class="cta-btn" onclick="showDiyRoute(currentResult)" style="padding:12px;font-size:14px;font-weight:600">Zelf doen</button>`;\n  html += `<button class="cta-btn" onclick="showProRoute(currentResult)" style="padding:12px;font-size:14px;font-weight:600;background:transparent;color:var(--text-primary);border:1.5px solid var(--border-light)">Laten doen</button>`;'

c1 = text.count(old_btns)
print(f"Buttons block found: {c1}")
text = text.replace(old_btns, new_btns)

# Remove the \u2190 back button from showDiyRoute
old_diy = 'margin-bottom:4px"><button onclick="showResults(currentResult)" style="background:none;border:none;cursor:pointer;padding:4px 0;font-size:16px;color:var(--text-secondary)">\\u2190</button></div>'
new_diy = 'margin-bottom:4px">'
c2 = text.count(old_diy)
print(f"Diy back button found: {c2}")
text = text.replace(old_diy, new_diy)

# Remove the \u2190 back button from showProRoute
old_pro = 'margin-bottom:4px"><button onclick="showResults(currentResult)" style="background:none;border:none;cursor:pointer;padding:4px 0;font-size:16px;color:var(--text-secondary)">\\u2190</button></div>'
new_pro = 'margin-bottom:4px">'
c3 = text.count(old_pro)
print(f"Pro back button found: {c3}")
text = text.replace(old_pro, new_pro)

with open(p, "wb") as f:
    f.write(text.encode("utf-8", errors="surrogateescape"))
print("done")