# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import numpy as np


def test_module_import():
    import easydiffraction.analysis.minimizers.bumps_de as MUT

    assert MUT.__name__ == 'easydiffraction.analysis.minimizers.bumps_de'


def test_type_info():
    from easydiffraction.analysis.minimizers.bumps_de import BumpsDEMinimizer
    from easydiffraction.analysis.minimizers.enums import MinimizerTypeEnum

    assert BumpsDEMinimizer.type_info.tag == MinimizerTypeEnum.BUMPS_DE


def test_is_subclass_of_bumps():
    from easydiffraction.analysis.minimizers.bumps import BumpsMinimizer
    from easydiffraction.analysis.minimizers.bumps_de import BumpsDEMinimizer

    assert issubclass(BumpsDEMinimizer, BumpsMinimizer)


def test_default_method():
    from easydiffraction.analysis.minimizers.bumps_de import BumpsDEMinimizer

    m = BumpsDEMinimizer()
    assert m.method == 'de'


def test_default_max_iterations():
    from easydiffraction.analysis.minimizers.bumps_de import BumpsDEMinimizer

    m = BumpsDEMinimizer()
    assert m.max_iterations == 1000


def test_default_name():
    from easydiffraction.analysis.minimizers.bumps_de import BumpsDEMinimizer
    from easydiffraction.analysis.minimizers.enums import MinimizerTypeEnum

    m = BumpsDEMinimizer()
    assert m.name == MinimizerTypeEnum.BUMPS_DE


def test_prepare_and_sync():
    from scipy.optimize import OptimizeResult

    from easydiffraction.analysis.minimizers.bumps_de import BumpsDEMinimizer

    class P:
        def __init__(self, name, value):
            self._minimizer_uid = name
            self._value = value
            self.free = True
            self.fit_min = -np.inf
            self.fit_max = np.inf
            self.uncertainty = None
            self.unique_name = name

        @property
        def value(self):
            return self._value

        @value.setter
        def value(self, v):
            self._value = v

        def _set_value_from_minimizer(self, v):
            self._value = v

        def _physical_lower_bound(self):
            return -np.inf

        def _physical_upper_bound(self):
            return np.inf

    m = BumpsDEMinimizer()
    params = [P('p1', 1.0)]

    # Prepare
    kwargs = m._prepare_solver_args(params)
    assert 'bumps_params' in kwargs
    assert kwargs['bumps_params'][0].name == 'p1'

    # Sync
    result = OptimizeResult(
        x=np.array([10.0]),
        dx=np.array([0.5]),
        success=True,
    )
    m._sync_result_to_parameters(params, result)
    assert params[0].value == 10.0
    assert params[0].uncertainty == 0.5
