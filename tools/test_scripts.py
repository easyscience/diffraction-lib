import pytest
import subprocess
from pathlib import Path

TUTORIALS = list(Path("tutorials").rglob("*.py"))

@pytest.mark.parametrize("script", TUTORIALS)
def test_script_runs(script):
    result = subprocess.run(
        ["python", str(script)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert result.returncode == 0, f"Failed script: {script}\n\n{result.stderr}"
