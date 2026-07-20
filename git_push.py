#!/usr/bin/env python3
"""Git add, commit, push."""
import subprocess, os
os.chdir("/home/team/shared")
subprocess.run(["git", "add", "-A"], check=True)
subprocess.run(["git", "commit", "-m", "Kosten Expert: accordion vervangen door Zelf/Laten secties met productkaarten, Gamma, Offerte"], check=True)
r = subprocess.run(["git", "push", "origin", "main"], capture_output=True, text=True)
print(r.stdout[-500:])
print(r.stderr[-500:])