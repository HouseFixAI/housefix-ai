#!/usr/bin/env python3
"""Replace showResults section as raw bytes. No encoding issues."""
import re

path = "/home/team/shared/backend/templates/index.html"
with open(path, "rb") as f:
    data = f.read()

# Find the section to replace (as bytes)
start_marker = b"function showResults(r) {"
end_marker = b"\nfunction renderProviders("
start_idx = data.find(start_marker)
end_idx = data.find(end_marker, start_idx)

if start_idx < 0 or end_idx < 0:
    print("ERROR: markers not found")
    exit(1)

# Find line start
func_start = data.rfind(b"\n", 0, start_idx)
func_start = func_start + 1  # start after the newline
func_end = end_idx

print(f"Replacing bytes {func_start}-{func_end}")

# Read the replacement text as bytes
with open("/home/team/shared/new_funcs_raw.txt", "rb") as f:
    replacement = f.read()

# Do the replacement
new_data = data[:func_start] + replacement + data[func_end:]

with open(path, "wb") as f:
    f.write(new_data)

print(f"Done. New size: {len(new_data)} bytes")