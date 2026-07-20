#!/usr/bin/env python3
import subprocess, os
os.chdir("/home/team/shared")
subprocess.run(["git", "add", "-A"])
subprocess.run(["git", "commit", "-m", "Kosten Expert toggle fix: opacity gecentraliseerd in toggleCostSection, consistent met Schade Expert"])
r = subprocess.run(["git", "push", "origin", "main"], capture_output=True, text=True)
print(r.stdout[-300:])