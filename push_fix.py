#!/usr/bin/env python3
import subprocess, os
os.chdir("/home/team/shared")
subprocess.run(["git", "add", "-A"])
subprocess.run(["git", "commit", "-m", "Schade Expert: cause/risk/urgency/advice velden toegevoegd aan SYSTEM_PROMPT, frontend fallback toont description"])
r = subprocess.run(["git", "push", "origin", "main"], capture_output=True, text=True)
print(r.stdout[-300:])
print(r.stderr[-300:])