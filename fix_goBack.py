#!/usr/bin/env python3
"""Add missing goBack function and glow CSS."""
p = "/home/team/shared/backend/templates/index.html"
with open(p, "r") as f:
    s = f.read()

# Add goBack function before analyze()
old = 'async function analyze() {'
new = 'function goBack() {\n  if (currentStep === "diy" || currentStep === "pro") {\n    showResults(currentResult);\n  } else {\n    goHome();\n  }\n}\nasync function analyze() {'
s = s.replace(old, new)

# Add glow CSS to backBtn
old_css = '#backBtn:hover { color: var(--terracotta); text-shadow: 0 0 8px rgba(196,98,74,0.4); }'
if old_css not in s:
    old_css_placeholder = 'transition: all 0.2s; width: 36px; justify-content: center; }'
    new_css = 'transition: all 0.2s; width: 36px; justify-content: center; }\n          #backBtn:hover { color: var(--terracotta); text-shadow: 0 0 8px rgba(196,98,74,0.4); }'
    s = s.replace(old_css_placeholder, new_css)

with open(p, "w") as f:
    f.write(s)
print("done")