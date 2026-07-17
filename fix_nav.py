#!/usr/bin/env python3
"""Remove duplicate nav. HTML has single backslash: \u2B05 - match that."""
p = "/home/team/shared/backend/templates/index.html"
with open(p, "rb") as f:
    data = f.read()
text = data.decode("utf-8", errors="surrogateescape")

# Match text with SINGLE backslash: \u2B05\uFE0F
# In Python source: \\u2B05 produces \u2B05 (1 backslash)
old_top = 'margin-bottom:12px"><button class="header-btn" onclick="showResults(currentResult)" style="color:var(--terracotta);font-size:13px;padding:6px 0;width:auto;gap:4px">\\u2B05\\uFE0F  Terug naar diagnose</button></div>'
new_top = 'margin-bottom:4px"><button onclick="showResults(currentResult)" style="background:none;border:none;cursor:pointer;padding:4px 0;font-size:16px;color:var(--text-secondary)">\\u2190</button></div>'

count_top = text.count(old_top)
print(f"Top back buttons found: {count_top}")
text = text.replace(old_top, new_top)

# Single backslash in bottom block too
old_bottom = '\\u2B05\\uFE0F  Terug naar diagnose</button>`;\n  html += `<button class="footer-btn-secondary" onclick="goHome()" style="text-align:center">Nieuwe scan</button>`;\n  html += `<button class="footer-btn-secondary" onclick="goHome()" style="text-align:center">Home</button>`;\n  html += `</div>'
new_bottom = 'height:60px"></div>'

count_bottom = text.count(old_bottom)
print(f"Bottom nav blocks found: {count_bottom}")
text = text.replace(old_bottom, new_bottom)

with open(p, "wb") as f:
    f.write(text.encode("utf-8", errors="surrogateescape"))
print("done")