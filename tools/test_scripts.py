"""Test runner for tutorial scripts in the 'tutorials' directory.

This test discovers and executes all Python scripts located under the 'tutorials'
directory to ensure they run without errors. Each script is executed in isolation
using runpy to simulate running as a standalone program.
"""

import runpy
from pathlib import Path

import pytest

# Discover all Python scripts under the 'tutorials' directory recursively
TUTORIALS = list(Path('tutorials').rglob('*.py'))


@pytest.mark.parametrize('script_path', TUTORIALS)
def test_script_runs(script_path: Path):
    """Execute a tutorial script and fail if it raises an exception.

    Each script is run in the context of __main__ to mimic standalone execution.
    """
    # Ensure the script path refers to an actual file
    assert script_path.is_file(), f'Expected file does not exist: {script_path}'

    # Ensure the script is located inside the 'tutorials' directory
    assert script_path.resolve().is_relative_to(Path('tutorials').resolve()), (
        f"Script is outside the 'tutorials' directory: {script_path}"
    )

    # Attempt to run the script using runpy
    try:
        runpy.run_path(str(script_path), run_name='__main__')
    except Exception as e:
        pytest.fail(f'{script_path}\n{e}')
