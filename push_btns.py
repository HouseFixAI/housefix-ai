#!/usr/bin/env python3
import subprocess, os
os.chdir("/home/team/shared")
subprocess.run(["git", "add", "-A"])
subprocess.run(["git", "commit", "-m", "Schade Expert: premium toggle-knoppen zonder emoji, subtiele kleur bij actief, geen terug-link"])
r = subprocess.run(["git", "push", "origin", "main"], capture_output=True, text=True)
print(r.stdout[-300:])