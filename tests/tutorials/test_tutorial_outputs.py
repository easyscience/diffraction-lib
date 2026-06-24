# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Assert that saved tutorial projects reproduce expected fit results.

This module runs *after* the tutorials have been executed (as scripts
via ``pixi run script-tests`` or as notebooks via
``pixi run notebook-tests``). Each tutorial saves its project under
``<artifact-root>/projects/<tutorial-name>/``; here we parse every
``analysis/analysis.edi`` and compare its fit-quality metrics and a few
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
from analysis_edi_reader import read_analysis_edi
from generate_baseline import PLATFORM_SENSITIVE
from generate_baseline import SEQUENTIAL_TUTORIALS
from generate_baseline import artifact_root

BASELINE = json.loads((Path(__file__).parent / 'baseline.json').read_text(encoding='utf-8'))

# Absolute tolerance floor, relevant only for values close to zero.
ABS_TOL = 1e-8


def _analysis_cif_path(name: str) -> Path:
    """Return the ``analysis.edi`` path for a saved tutorial project."""
    return artifact_root() / 'projects' / name / 'analysis' / 'analysis.edi'


def _artifacts_present() -> bool:
    """Return whether any tutorial project has been saved."""
    projects_dir = artifact_root() / 'projects'
    if not projects_dir.is_dir():
        return False
    # Tutorial-saved projects only; downloaded ``proj-`` archives don't count.
    return any(
        not path.parents[1].name.startswith('proj-')
        for path in projects_dir.glob('*/analysis/analysis.edi')
    )


pytestmark = pytest.mark.skipif(
    not _artifacts_present(),
    reason='No tutorial artifacts found; run script-tests or notebook-tests first.',
)


def _assert_close(actual: float | None, expected: float, rtol: float, label: str) -> None:
    """Assert *actual* matches *expected* within a relative tolerance."""
    assert actual is not None, f'{label}: value missing from analysis.edi'
    assert math.isclose(actual, expected, rel_tol=rtol, abs_tol=ABS_TOL), (
        f'{label}: {actual} != {expected} (rel_tol={rtol})'
    )


@pytest.mark.parametrize('name', sorted(BASELINE))
def test_tutorial_output(name: str) -> None:
    """Check one tutorial's saved analysis.edi against the baseline."""
    expected = BASELINE[name]
    cif_path = _analysis_cif_path(name)
    assert cif_path.is_file(), f"Missing {cif_path}; tutorial '{name}' did not save its project."

    cif = read_analysis_edi(cif_path)

    # result_kind reflects the minimizer type; it is reproducible
    # across platforms, so it is always checked.
    assert cif.result_kind == expected['result_kind'], (
        f"{name}: result_kind '{cif.result_kind}' != expected '{expected['result_kind']}'"
    )

    # Some tutorials (e.g. ed-7 on the compiled crysfml backend)
    # produce fit metrics that are not reproducible across CPU arch
    # or BLAS; confirm they ran and saved, but skip the numbers.
    if name in PLATFORM_SENSITIVE:
        pytest.skip('platform-sensitive')

    rtol = expected['rtol']
    _assert_close(
        cif.scalar('reduced_chi_square'),
        expected['reduced_chi_square'],
        rtol,
        f'{name}: reduced_chi_square',
    )

    for scalar_name in ('r_factor_all', 'wr_factor_all'):
        if scalar_name in expected:
            _assert_close(
                cif.scalar(scalar_name),
                expected[scalar_name],
                rtol,
                f'{name}: {scalar_name}',
            )

    for param_name, exp_value in expected['parameters'].items():
        assert param_name in cif.fit_parameters, (
            f"{name}: parameter '{param_name}' missing from analysis.edi"
        )
        _assert_close(
            cif.parameter_value(param_name),
            exp_value,
            rtol,
            f'{name}: {param_name}',
        )


@pytest.mark.parametrize('name', sorted(SEQUENTIAL_TUTORIALS))
def test_sequential_tutorial_saved(name: str) -> None:
    """Check a sequential-fit tutorial saved a sequential analysis.edi.

    Sequential fits run one refinement per measured point and write no
    single ``_fit_result`` block, so they cannot go through the scalar
    baseline in ``test_tutorial_output``. This guards the persistence of
    that workflow instead: the project must save, and its analysis must
    record ``_fitting_mode.type sequential``.
    """
    cif_path = _analysis_cif_path(name)
    assert cif_path.is_file(), f"Missing {cif_path}; tutorial '{name}' did not save its project."

    text = cif_path.read_text(encoding='utf-8')
    assert '_fitting_mode.type sequential' in text, f'{name}: analysis.edi is not a sequential fit'
