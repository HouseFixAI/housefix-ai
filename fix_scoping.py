#!/usr/bin/env python3
"""Fix function scoping without losing carousel/switch changes."""
p = "/home/team/shared/backend/templates/index.html"
with open(p, "r") as f:
    s = f.read()

# Remove duplicate showDamageExpert if exists
idx1 = s.find('function showDamageExpert')
idx2 = s.find('function showDamageExpert', idx1 + 10)
if idx2 > 0:
    prev = s.rfind('}', idx1, idx2)
    if prev > idx1:
        s = s[:prev] + s[idx2:]
        print("Removed duplicate showDamageExpert")

# Fix scoping: showDamageExpert should be inside renderResults
# Old: currentStep = "diagnose";\n}}\nfunction showDamageExpert
# New: currentStep = "diagnose";\n  }\n  function showDamageExpert
old1 = '  currentStep = "diagnose";\n}}\nfunction showDamageExpert'
new1 = '  currentStep = "diagnose";\n  }\n  function showDamageExpert'
c1 = s.count(old1)
print(f"Pattern 1 found: {c1}")
s = s.replace(old1, new1)

# Fix scoping: showRepairExpert should be inside renderResults  
old2 = '  currentStep = "diagnose";\n}\nfunction showRepairExpert'
new2 = '  currentStep = "diagnose";\n  }\n  function showRepairExpert'
c2 = s.count(old2)
print(f"Pattern 2 found: {c2}")
s = s.replace(old2, new2)

# Fix showDiyRoute back to top level (outside renderResults)
# After repair expert closes with 2-space indent, showDiyRoute should be at 0 indent
old3 = '  currentStep = "diagnose";\n  }\n  function showDiyRoute'
new3 = '  currentStep = "diagnose";\n  }\nfunction showDiyRoute'
c3 = s.count(old3)
print(f"Pattern 3 found: {c3}")
s = s.replace(old3, new3)

with open(p, "w") as f:
    f.write(s)
print("done")