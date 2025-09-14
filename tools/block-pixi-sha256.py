#! /usr/bin/env python3
import subprocess, sys

diff = subprocess.run(
    ["git", "diff", "--cached", "pixi.lock"],
    capture_output=True, text=True
).stdout

if diff:
    sha_lines = [l for l in diff.splitlines() if l.startswith(("+", "-")) and "sha256:" in l]
    other_lines = [l for l in diff.splitlines() if l.startswith(("+", "-")) and "sha256:" not in l]
    if sha_lines and not other_lines:
        print("❌ Aborting commit: pixi.lock has only sha256 changes (likely from editable easydiffraction).")
        print("   Run: git restore --staged pixi.lock")
        sys.exit(1)

sys.exit(0)