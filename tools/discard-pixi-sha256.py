#!/usr/bin/env python3
import subprocess
import sys

# Get staged diff for pixi.lock
diff = subprocess.run(
    ["git", "diff", "--cached", "pixi.lock"],
    capture_output=True, text=True
).stdout

if not diff:
    sys.exit(0)  # nothing staged

# Collect added/removed lines
lines = [l for l in diff.splitlines() if l.startswith(("+", "-"))]

# Filter out sha256 changes under easydiffraction
sha_changes = [l for l in lines if "sha256:" in l and "easydiffraction" in diff]
other_changes = [l for l in lines if "sha256:" not in l]

if sha_changes and not other_changes:
    print("⚠️  Discarding pixi.lock because only easydiffraction sha256 changed")
    subprocess.run(["git", "restore", "--staged", "pixi.lock"])
    subprocess.run(["git", "restore", "pixi.lock"])
    sys.exit(0)

sys.exit(0)