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

# (id, structure download slug, experiment download slug, engine)
SCENARIOS = [
    ('neut-cwl-pd-cryspy', 'struct-lbco', 'expt-lbco-hrpt', 'cryspy'),
    ('neut-cwl-pd-crysfml', 'struct-lbco', 'expt-lbco-hrpt', 'crysfml'),
]


@pytest.mark.nightly
@pytest.mark.parametrize(
    ('label', 'structure_id', 'experiment_id', 'engine'),
    SCENARIOS,
    ids=[scenario[0] for scenario in SCENARIOS],
)
def test_calculate_pattern_benchmark(benchmark, label, structure_id, experiment_id, engine):
    """Benchmark a single pattern calculation for one experiment x engine."""
    import easydiffraction as edi
    from easydiffraction.analysis.fit_helpers.metrics import get_reliability_inputs

    project = edi.Project()
    project.structures.add_from_cif_path(edi.download_data(structure_id, destination='data'))
    project.experiments.add_from_edi_path(edi.download_data(experiment_id, destination='data'))

    experiment = project.experiments['hrpt']
    experiment.calculator.type = engine

    def _calculate():
        return get_reliability_inputs(project.structures, [experiment])

    result = benchmark(_calculate)

    assert result is not None
