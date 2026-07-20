#!/usr/bin/env python3
"""Install Flask and start server."""
import subprocess, time, os

# Install
r = subprocess.run(["pip3", "install", "flask", "flask-cors"], capture_output=True, text=True, timeout=120)
print(r.stdout[-200:])
print(r.stderr[-200:])

# Kill old server
os.system("pkill -f 'python3 main.py' 2>/dev/null")
time.sleep(0.5)

# Start server
os.chdir("/home/team/shared/backend")
proc = subprocess.Popen(["python3", "main.py"], stdout=open("/tmp/backend.log","w"), stderr=subprocess.STDOUT)
time.sleep(2)

# Check health
r2 = subprocess.run(["curl", "-s", "http://localhost:8000/api/health"], capture_output=True, text=True, timeout=10)
print("Health:", r2.stdout.strip() or "no response")