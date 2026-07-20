#!/usr/bin/env python3
"""Replace last result pill with subtle link - exact match."""
import subprocess

p = "/home/team/shared/backend/templates/index.html"
with open(p, "rb") as f:
    raw = f.read()

# Find showLastResultBadge function
start_marker = b'function showLastResultBadge() {'
end_marker = b'function dismissLastResult()'

idx_start = raw.find(start_marker)
idx_end = raw.find(end_marker)

if idx_start < 0 or idx_end < 0:
    print("ERROR: markers not found")
    exit(1)

old_bytes = raw[idx_start:idx_end]
print(f"Old function: {len(old_bytes)} bytes")

new_bytes = b'''function showLastResultBadge() {
  const existing = document.getElementById("lastResultLink");
  if (existing) existing.remove();
  if (!lastResult) return;
  const container = document.querySelector(".dg-3");
  if (!container) return;
  const link = document.createElement("div");
  link.id = "lastResultLink";
  link.style.cssText = "margin-top:-8px;margin-bottom:14px;text-align:center;font-size:12px;color:var(--text-muted);cursor:pointer;transition:color 0.2s";
  link.innerHTML = \'<span style="border-bottom:1px solid rgba(255,255,255,0.1);padding:2px 4px">\\u2190 Verder met vorige analyse</span>\';
  link.onmouseover = function() { this.style.color = "var(--text-secondary)"; };
  link.onmouseout = function() { this.style.color = "var(--text-muted)"; };
  link.onclick = function() {
    if (lastResult) {
      link.remove();
      document.getElementById("screenDashboard").classList.add("hidden");
      document.getElementById("resultsWrap").classList.add("active");
      document.querySelector(".dash-footer").style.display = "none";
      renderResults(lastResultIntent || "damage", lastResult);
    }
  };
  container.parentNode.insertBefore(link, container);
}
'''

raw = raw[:idx_start] + new_bytes + raw[idx_end:]

with open(p, "wb") as f:
    f.write(raw)
print("showLastResultBadge replaced")

r = subprocess.run(["node", "-e", "const fs=require('fs');const s=fs.readFileSync('/home/team/shared/backend/templates/index.html','utf8');const m=s.match(/<script>([\\s\\S]*?)<\\/script>/);try{new Function(m[1]);console.log('JS_OK')}catch(e){console.log('Error: '+e.message)}"], capture_output=True, text=True)
print("JS:", r.stdout.strip())