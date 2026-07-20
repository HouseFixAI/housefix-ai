#!/usr/bin/env python3
import subprocess, os
os.chdir("/home/team/shared")
subprocess.run(["git", "add", "-A"])
subprocess.run(["git", "commit", "-m", "Reparatie Expert: premium klikbare Zelf/Laten flow met tijdsindicatie en moeilijkheidsgraad"])
r = subprocess.run(["git", "push", "origin", "main"], capture_output=True, text=True)
print(r.stdout[-300:])
print(r.stderr[-300:])