# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

import collections
import types

import numpy as np


def test_module_import():
    import easydiffraction.analysis.minimizers.lmfit_leastsq as MUT

    assert MUT.__name__ == 'easydiffraction.analysis.minimizers.lmfit_leastsq'


def test_type_info():
    from easydiffraction.analysis.minimizers.enums import MinimizerTypeEnum
    from easydiffraction.analysis.minimizers.lmfit_leastsq import LmfitLeastsqMinimizer

    assert LmfitLeastsqMinimizer.type_info.tag == MinimizerTypeEnum.LMFIT_LEASTSQ


def test_is_subclass_of_lmfit():
    from easydiffraction.analysis.minimizers.lmfit import LmfitMinimizer
    from easydiffraction.analysis.minimizers.lmfit_leastsq import LmfitLeastsqMinimizer

    assert issubclass(LmfitLeastsqMinimizer, LmfitMinimizer)


def test_default_method():
    from easydiffraction.analysis.minimizers.lmfit_leastsq import LmfitLeastsqMinimizer

    m = LmfitLeastsqMinimizer()
    assert m.method == 'leastsq'


def test_prepare_and_sync(monkeypatch):
    from easydiffraction.analysis.minimizers.lmfit_leastsq import LmfitLeastsqMinimizer

    class P:
        def __init__(self, name, value, *, free=True, lo=-np.inf, hi=np.inf):
            self._minimizer_uid = name
            self._value = value
            self.free = free
            self.fit_min = lo
            self.fit_max = hi
            self.uncertainty = None

        @property
        def value(self):
            return self._value

        @value.setter
        def value(self, v):
            self._value = v

        def _set_value_from_minimizer(self, v):
            self._value = v

    class FakeParam:
        def __init__(self, value, stderr=None):
            self.value = value
            self.stderr = stderr

    class FakeParams(collections.UserDict):
        def add(self, name, value, vary, min, max):
            self[name] = types.SimpleNamespace(value=value, vary=vary, min=min, max=max)

    class FakeResult:
        def __init__(self):
            self.params = {'p1': FakeParam(10.0, stderr=0.5)}
            self.success = True

    import easydiffraction.analysis.minimizers.lmfit as lm

    monkeypatch.setattr(
        lm,
        'lmfit',
        types.SimpleNamespace(Parameters=FakeParams, minimize=lambda *a, **k: FakeResult()),
    )

    minim = LmfitLeastsqMinimizer()
    params = [P('p1', 1.0)]

    kwargs = minim._prepare_solver_args(params)
    res = minim._run_solver(lambda *a, **k: np.array([0.0]), **kwargs)
    minim._sync_result_to_parameters(params, res)

    assert params[0].value == 10.0
    assert params[0].uncertainty == 0.5
