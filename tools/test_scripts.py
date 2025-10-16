"""Test runner for tutorial scripts in the 'tutorials' directory.

This test discovers and executes all Python scripts located under the
'tutorials' directory to ensure they run without errors. Each script is
executed in isolation using runpy to simulate running as a standalone
program.
"""

import runpy
from pathlib import Path

import pytest

# Mark this module as 'functional' so it's excluded by default
# (see pytest.ini)
pytestmark = pytest.mark.functional

# Discover tutorial scripts, excluding temporary checkpoint files
TUTORIALS = [p for p in Path('tutorials').rglob('*.py') if '.ipynb_checkpoints' not in p.parts]


@pytest.mark.parametrize('script_path', TUTORIALS)
def test_script_runs(script_path: Path):
    """Execute a tutorial script and fail if it raises an exception.

    Each script is run in the context of __main__ to mimic standalone
    execution.
    """
    try:
        runpy.run_path(str(script_path), run_name='__main__')
    except Exception as e:
        pytest.fail(f'{script_path}\n{e}')
