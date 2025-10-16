# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

import numpy as np


def test_module_import():
    import easydiffraction.analysis.calculators.base as MUT

    assert MUT.__name__ == 'easydiffraction.analysis.calculators.base'


def test_calculator_base_get_valid_linked_phases_filters_missing():
    from easydiffraction.analysis.calculators.base import CalculatorBase

    class DummyCalc(CalculatorBase):
        @property
        def name(self):
            return 'dummy'

        @property
        def engine_imported(self):
            return True

        def calculate_structure_factors(self, sample_model, experiment):
            pass

        def _calculate_single_model_pattern(self, sample_model, experiment, called_by_minimizer):
            return np.zeros_like(experiment.datastore.x)

    class DummyLinked:
        def __init__(self, entry_name):
            self._identity = type('I', (), {'category_entry_name': entry_name})
            self.scale = type('S', (), {'value': 1.0})
            self.id = type('ID', (), {'value': entry_name})

    class DummyStore:
        def __init__(self, n=5):
            self.x = np.arange(n, dtype=float)

    class DummyExperiment:
        def __init__(self, linked):
            self.linked_phases = linked
            self.datastore = DummyStore()

            def _public():
                return []

            self._public_attrs = _public

    class DummySampleModels(dict):
        @property
        def names(self):
            return list(self.keys())

    calc = DummyCalc()
    expt = DummyExperiment([DummyLinked('present'), DummyLinked('absent')])
    sm = DummySampleModels({'present': object()})
    valid = calc._get_valid_linked_phases(sm, expt)
    assert len(valid) == 1 and valid[0]._identity.category_entry_name == 'present'
