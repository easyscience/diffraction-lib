# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Performance benchmarks for diffraction-pattern calculation.

Nightly-tier: these run real calculation engines and are excluded from
the per-push and per-PR runs. Each scenario is keyed by
``beam_mode x radiation_probe x engine`` so regressions can be localised.
Informational only for now — no regression gate yet (see ADR
test-suite-and-validation §7). Run with ``pixi run benchmarks``.
"""

from __future__ import annotations

import pytest

# (id, structure download id, experiment download id, engine)
SCENARIOS = [
    ('neut-cwl-pd-cryspy', 1, 2, 'cryspy'),
    ('neut-cwl-pd-crysfml', 1, 2, 'crysfml'),
]


@pytest.mark.nightly
@pytest.mark.parametrize(
    ('label', 'structure_id', 'experiment_id', 'engine'),
    SCENARIOS,
    ids=[scenario[0] for scenario in SCENARIOS],
)
def test_calculate_pattern_benchmark(benchmark, label, structure_id, experiment_id, engine):
    """Benchmark a single pattern calculation for one experiment x engine."""
    import easydiffraction as ed
    from easydiffraction.analysis.fit_helpers.metrics import get_reliability_inputs

    project = ed.Project()
    project.structures.add_from_cif_path(ed.download_data(id=structure_id, destination='data'))
    project.experiments.add_from_cif_path(ed.download_data(id=experiment_id, destination='data'))

    experiment = project.experiments['hrpt']
    experiment.calculator.type = engine

    def _calculate():
        return get_reliability_inputs(project.structures, [experiment])

    result = benchmark(_calculate)

    assert result is not None
