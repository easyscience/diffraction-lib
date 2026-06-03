# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Generate the committed baseline for the tutorial-output tests.

Run the tutorials first (``pixi run script-tests`` or
``pixi run notebook-tests``) so each saved project exists under
``<artifact-root>/projects/``. Then run this script to (re)write
``baseline.json`` from the freshly produced ``analysis.cif`` files::

    pixi run python tests/tutorials/generate_baseline.py

Review the resulting diff before committing; tweak per-tutorial
tolerances or tracked parameters by editing ``baseline.json`` directly.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from analysis_cif_reader import AnalysisCif
from analysis_cif_reader import read_analysis_cif

# Relative tolerances used when comparing against the baseline. Bayesian
# (MCMC) fits are seeded but still vary slightly more than deterministic
# refinements, so they get a looser bound.
DETERMINISTIC_RTOL = 0.02
BAYESIAN_RTOL = 0.10

# Optional deterministic fit-quality scalars to track when present.
OPTIONAL_SCALARS = ('R_factor_all', 'wR_factor_all')

# Number of refined parameters to track per tutorial (cell lengths and
# phase scales preferred, topped up from the front of the loop).
KEY_PARAMETER_COUNT = 2
ROUND_DIGITS = 6

REPO_ROOT = Path(__file__).resolve().parents[2]
BASELINE_PATH = Path(__file__).resolve().parent / 'baseline.json'


def artifact_root() -> Path:
    """Return the configured tutorial artifact root directory."""
    configured = os.environ.get('EASYDIFFRACTION_ARTIFACT_ROOT')
    if configured:
        return Path(configured) if Path(configured).is_absolute() else REPO_ROOT / configured
    return REPO_ROOT / 'tmp' / 'tutorials'


def _is_key_parameter(name: str) -> bool:
    """Return whether *name* is a lattice length or a phase scale."""
    return '.cell.length_' in name or name.endswith('.scale')


def select_key_parameters(cif: AnalysisCif) -> dict[str, float]:
    """Return the tracked refined parameter values for one project."""
    names = list(cif.fit_parameters)
    selected = [name for name in names if _is_key_parameter(name)]
    for name in names:
        if len(selected) >= KEY_PARAMETER_COUNT:
            break
        if name not in selected:
            selected.append(name)
    ordered = [name for name in names if name in set(selected)]
    return {name: round(cif.parameter_value(name), ROUND_DIGITS) for name in ordered}


def build_entry(cif: AnalysisCif) -> dict | None:
    """Build a baseline entry, or ``None`` if the project has no fit."""
    reduced_chi_square = cif.scalar('reduced_chi_square')
    if reduced_chi_square is None or reduced_chi_square <= 0:
        return None

    kind = cif.result_kind or 'deterministic'
    entry: dict = {
        'result_kind': kind,
        'rtol': BAYESIAN_RTOL if kind == 'bayesian' else DETERMINISTIC_RTOL,
        'reduced_chi_square': round(reduced_chi_square, ROUND_DIGITS),
    }
    for scalar_name in OPTIONAL_SCALARS:
        value = cif.scalar(scalar_name)
        if value is not None:
            entry[scalar_name] = round(value, ROUND_DIGITS)
    entry['parameters'] = select_key_parameters(cif)
    return entry


def collect_baseline(root: Path) -> dict[str, dict]:
    """Build baseline entries for every saved project under *root*."""
    projects_dir = root / 'projects'
    baseline: dict[str, dict] = {}
    for cif_path in sorted(projects_dir.glob('*/analysis/analysis.cif')):
        name = cif_path.parents[1].name
        if not name.startswith('ed_'):
            continue
        entry = build_entry(read_analysis_cif(cif_path))
        if entry is not None:
            baseline[name] = entry
    return baseline


def main() -> None:
    """Write ``baseline.json`` from the current tutorial artifacts."""
    root = artifact_root()
    baseline = collect_baseline(root)
    if not baseline:
        msg = f'No tutorial projects with fit results found under {root / "projects"}.'
        raise SystemExit(msg)

    ordered = {name: baseline[name] for name in sorted(baseline)}
    BASELINE_PATH.write_text(json.dumps(ordered, indent=2) + '\n', encoding='utf-8')
    print(f'Wrote {len(ordered)} tutorial baselines to {BASELINE_PATH}')


if __name__ == '__main__':
    main()
