#!/usr/bin/env python3
import subprocess, sys, os

os.chdir("/home/team/shared")
result = subprocess.run(
    ["git", "diff", "--name-only", "HEAD"],
    capture_output=True, text=True, timeout=30
)
with open("/tmp/git_diff_output.txt", "w") as f:
    f.write(f"stdout: {result.stdout}\n")
    f.write(f"stderr: {result.stderr}\n")
    f.write(f"returncode: {result.returncode}\n")
print("DONE")