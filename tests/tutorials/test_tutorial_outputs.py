# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Assert that saved tutorial projects reproduce expected fit results.

This module runs *after* the tutorials have been executed (as scripts
via ``pixi run script-tests`` or as notebooks via
``pixi run notebook-tests``). Each tutorial saves its project under
``<artifact-root>/projects/ed_<n>_<name>/``; here we parse every
``analysis/analysis.cif`` and compare its fit-quality metrics and a few
refined parameter values against the committed ``baseline.json``.

If no tutorial artifacts are present the whole module is skipped, so the
file is safe to collect in a plain ``pytest`` run that did not first
execute the tutorials.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from analysis_cif_reader import read_analysis_cif
from generate_baseline import artifact_root

BASELINE = json.loads((Path(__file__).parent / 'baseline.json').read_text(encoding='utf-8'))

# Absolute tolerance floor, relevant only for values close to zero.
ABS_TOL = 1e-8


def _analysis_cif_path(name: str) -> Path:
    """Return the ``analysis.cif`` path for a saved tutorial project."""
    return artifact_root() / 'projects' / name / 'analysis' / 'analysis.cif'


def _artifacts_present() -> bool:
    """Return whether any tutorial project has been saved."""
    projects_dir = artifact_root() / 'projects'
    return projects_dir.is_dir() and any(projects_dir.glob('ed_*/analysis/analysis.cif'))


pytestmark = pytest.mark.skipif(
    not _artifacts_present(),
    reason='No tutorial artifacts found; run script-tests or notebook-tests first.',
)


def _assert_close(actual: float | None, expected: float, rtol: float, label: str) -> None:
    """Assert *actual* matches *expected* within a relative tolerance."""
    assert actual is not None, f'{label}: value missing from analysis.cif'
    assert math.isclose(actual, expected, rel_tol=rtol, abs_tol=ABS_TOL), (
        f'{label}: {actual} != {expected} (rel_tol={rtol})'
    )


@pytest.mark.parametrize('name', sorted(BASELINE))
def test_tutorial_output(name: str) -> None:
    """Check one tutorial's saved analysis.cif against the baseline."""
    expected = BASELINE[name]
    cif_path = _analysis_cif_path(name)
    assert cif_path.is_file(), f"Missing {cif_path}; tutorial '{name}' did not save its project."

    cif = read_analysis_cif(cif_path)
    rtol = expected['rtol']

    _assert_close(
        cif.scalar('reduced_chi_square'),
        expected['reduced_chi_square'],
        rtol,
        f'{name}: reduced_chi_square',
    )

    for scalar_name in ('R_factor_all', 'wR_factor_all'):
        if scalar_name in expected:
            _assert_close(
                cif.scalar(scalar_name),
                expected[scalar_name],
                rtol,
                f'{name}: {scalar_name}',
            )

    for param_name, exp_value in expected['parameters'].items():
        assert param_name in cif.fit_parameters, (
            f"{name}: parameter '{param_name}' missing from analysis.cif"
        )
        _assert_close(
            cif.parameter_value(param_name),
            exp_value,
            rtol,
            f'{name}: {param_name}',
        )
