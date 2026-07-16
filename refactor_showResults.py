#!/usr/bin/env python3
"""Refactor showResults() — replace by position. Proper Unicode handling."""
import subprocess

path = "/home/team/shared/backend/templates/index.html"
with open(path, "r", encoding="utf-8") as f:
    html = f.read()

# Find the showResults function
start_marker = "function showResults(r) {"
end_marker = "\nfunction toggleProviders()"

start_idx = html.find(start_marker)
end_idx = html.find(end_marker, start_idx)

if start_idx < 0 or end_idx < 0:
    print("ERROR: markers not found")
    exit(1)

func_start = html.rfind("\n", 0, start_idx) + 1
func_end = end_idx

old_func = html[func_start:func_end]
print(f"Found showResults at {func_start}-{func_end}, len={len(old_func)}")

# Read the new function from a separate file
new_func_path = "/home/team/shared/new_showResults.txt"
with open(new_func_path, "r", encoding="utf-8") as f:
    new_func = f.read()

# Replace
html = html[:func_start] + new_func + html[func_end:]

with open(path, "w", encoding="utf-8") as f:
    f.write(html)

# Verify JS syntax
result = subprocess.run(
    ["node", "-e",
     "const fs=require('fs');const s=fs.readFileSync('" + path + "','utf8');"
     "const m=s.match(/<script>([\\s\\S]*?)<\\/script>/);"
     "if(!m){process.exit(1)}"
     "try{new Function(m[1]);console.log('JS_OK')}catch(e){console.log('JS_ERROR:',e.message);process.exit(1)}"],
    capture_output=True, text=True, shell=True
)
print(result.stdout.strip())
if result.returncode != 0:
    print("STDERR:", result.stderr.strip())
    exit(1)