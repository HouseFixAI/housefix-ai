#!/usr/bin/env python3
"""Final cleanup: remove empty wrapper div left from back button removal."""
p = "/home/team/shared/backend/templates/index.html"
with open(p, "r") as f:
    s = f.read()

# Fix DIY: remove empty wrapper div
s = s.replace(
    'let html = `<div style="margin-bottom:4px">`;\n  if (diyCost !== "\\u2014") {',
    'let html = ``;\n  if (diyCost !== "\\u2014") {'
)

# Fix PRO: same issue
s = s.replace(
    'let html = `<div style="margin-bottom:4px">`;\n  if (proCost !== "\\u2014") {',
    'let html = ``;\n  if (proCost !== "\\u2014") {'
)

with open(p, "w") as f:
    f.write(s)
print("done")