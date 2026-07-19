#!/usr/bin/env python3
"""Remove duplicate showDamageExpert and fix JS syntax."""
p = "/home/team/shared/backend/templates/index.html"
with open(p, "r") as f:
    s = f.read()

# Find two occurrences of 'function showDamageExpert'
idx1 = s.find('function showDamageExpert(r) {')
idx2 = s.find('function showDamageExpert(r) {', idx1 + 10)
if idx2 > 0:
    # Find the closing } before the second occurrence
    # Search backwards from idx2
    prev_close = s.rfind('}', idx1, idx2)
    if prev_close > idx1:
        # Remove from prev_close to idx2
        s = s[:prev_close] + s[idx2:]
        with open(p, "w") as f:
            f.write(s)
        print(f"Removed duplicate. prev_close={prev_close}, idx2={idx2}")
else:
    print("No duplicate found")

# Count occurrences again
print(f"showDamageExpert count: {s.count('function showDamageExpert')}")
print(f"showRepairExpert count: {s.count('function showRepairExpert')}")