#!/usr/bin/env python3
import urllib.request, json, sys

results = []

try:
    resp = urllib.request.urlopen("http://localhost:8000/api/health", timeout=5)
    data = resp.read().decode()
    results.append(f"Health: {data}")
except Exception as e:
    results.append(f"Health error: {e}")

try:
    resp = urllib.request.urlopen("http://localhost:8000/", timeout=5)
    html = resp.read().decode()
    if "scrollable" in html:
        results.append("WARNING: 'scrollable' still in HTML!")
    if "housefix" in html.lower() or "HouseFix" in html:
        results.append("Frontend OK - HouseFix found")
    results.append(f"HTML size: {len(html)} bytes")
except Exception as e:
    results.append(f"Frontend error: {e}")

with open("/home/team/shared/test_results.txt", "w") as f:
    f.write("\n".join(results))
sys.exit(0)