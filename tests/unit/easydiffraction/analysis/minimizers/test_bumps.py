# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import types
from unittest.mock import MagicMock
from unittest.mock import patch

import numpy as np
import pytest


def test_module_import():
    import easydiffraction.analysis.minimizers.bumps as MUT

    assert MUT.__name__ == 'easydiffraction.analysis.minimizers.bumps'


def test_type_info():
    from easydiffraction.analysis.minimizers.bumps import BumpsMinimizer
    from easydiffraction.analysis.minimizers.enums import MinimizerTypeEnum

    assert BumpsMinimizer.type_info.tag == MinimizerTypeEnum.BUMPS


def test_default_method():
    from easydiffraction.analysis.minimizers.bumps import BumpsMinimizer

    m = BumpsMinimizer()
    assert m.method == 'lm'


def test_default_max_iterations():
    from easydiffraction.analysis.minimizers.bumps import BumpsMinimizer

    m = BumpsMinimizer()
    assert m.max_iterations == 1000


def test_is_subclass_of_base():
    from easydiffraction.analysis.minimizers.base import MinimizerBase
    from easydiffraction.analysis.minimizers.bumps import BumpsMinimizer

    assert issubclass(BumpsMinimizer, MinimizerBase)


# -- Helpers for fake parameters -----------------------------------------------


class FakeParam:
    """Minimal stand-in for an EasyDiffraction parameter."""

    def __init__(self, uid, value, *, fit_min=-np.inf, fit_max=np.inf):
        self._minimizer_uid = uid
        self._value = value
        self.free = True
        self.fit_min = fit_min
        self.fit_max = fit_max
        self.uncertainty = None
        self.unique_name = uid

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


# -- _prepare_solver_args tests ------------------------------------------------


def test_prepare_solver_args_returns_bumps_params():
    from easydiffraction.analysis.minimizers.bumps import BumpsMinimizer

    m = BumpsMinimizer()
    params = [FakeParam('a', 1.0), FakeParam('b', 2.0)]
    kwargs = m._prepare_solver_args(params)

    assert 'bumps_params' in kwargs
    bp = kwargs['bumps_params']
    assert len(bp) == 2
    assert bp[0].name == 'a'
    assert bp[0].value == 1.0
    assert bp[1].name == 'b'
    assert bp[1].value == 2.0


def test_prepare_solver_args_applies_fit_bounds():
    from easydiffraction.analysis.minimizers.bumps import BumpsMinimizer

    m = BumpsMinimizer()
    params = [FakeParam('x', 5.0, fit_min=0.0, fit_max=10.0)]
    kwargs = m._prepare_solver_args(params)
    bp = kwargs['bumps_params'][0]
    assert bp.bounds == (0.0, 10.0)


def test_prepare_solver_args_falls_back_to_physical_bounds():
    from easydiffraction.analysis.minimizers.bumps import BumpsMinimizer

    class PhysParam(FakeParam):
        def _physical_lower_bound(self):
            return 0.0

        def _physical_upper_bound(self):
            return 100.0

    m = BumpsMinimizer()
    params = [PhysParam('x', 5.0)]
    kwargs = m._prepare_solver_args(params)
    bp = kwargs['bumps_params'][0]
    assert bp.bounds == (0.0, 100.0)


# -- _EasyDiffractionFitness tests --------------------------------------------


def test_fitness_parameters():
    from easydiffraction.analysis.minimizers.bumps import _EasyDiffractionFitness

    bp1 = MagicMock(name='p1', value=1.0)
    bp1.name = 'p1'
    bp2 = MagicMock(name='p2', value=2.0)
    bp2.name = 'p2'

    fitness = _EasyDiffractionFitness([bp1, bp2], lambda v: v)
    pdict = fitness.parameters()
    assert set(pdict.keys()) == {'p1', 'p2'}


def test_fitness_residuals():
    from bumps.parameter import Parameter as BumpsParameter

    from easydiffraction.analysis.minimizers.bumps import _EasyDiffractionFitness

    bp = BumpsParameter(value=3.0, name='a')
    obj = lambda values: np.array([values[0] - 1.0])  # noqa: E731
    fitness = _EasyDiffractionFitness([bp], obj)
    r = fitness.residuals()
    np.testing.assert_array_almost_equal(r, [2.0])


def test_fitness_nllf():
    from bumps.parameter import Parameter as BumpsParameter

    from easydiffraction.analysis.minimizers.bumps import _EasyDiffractionFitness

    bp = BumpsParameter(value=4.0, name='a')
    obj = lambda values: np.array([2.0, 2.0])  # noqa: E731
    fitness = _EasyDiffractionFitness([bp], obj)
    nllf = fitness.nllf()
    assert nllf == pytest.approx(4.0)  # 0.5 * (4 + 4)


def test_fitness_numpoints_after_nllf():
    from bumps.parameter import Parameter as BumpsParameter

    from easydiffraction.analysis.minimizers.bumps import _EasyDiffractionFitness

    bp = BumpsParameter(value=0.0, name='a')
    obj = lambda values: np.array([1.0, 2.0, 3.0])  # noqa: E731
    fitness = _EasyDiffractionFitness([bp], obj)
    assert fitness.numpoints() == 0  # before calling nllf
    fitness.nllf()
    assert fitness.numpoints() == 3


def test_fitness_update_is_noop():
    from easydiffraction.analysis.minimizers.bumps import _EasyDiffractionFitness

    fitness = _EasyDiffractionFitness([], lambda v: np.array([]))
    fitness.update()  # should not raise


# -- _run_solver tests ---------------------------------------------------------


def test_run_solver_returns_optimize_result():
    from scipy.optimize import OptimizeResult

    from easydiffraction.analysis.minimizers.bumps import BumpsMinimizer

    m = BumpsMinimizer()

    fake_x = np.array([1.5, 2.5])

    fake_fitter = types.SimpleNamespace(id='lm')

    with (
        patch('easydiffraction.analysis.minimizers.bumps.FitDriver') as mock_driver_cls,
        patch('easydiffraction.analysis.minimizers.bumps.FitProblem'),
        patch('easydiffraction.analysis.minimizers.bumps.FITTERS', [fake_fitter]),
        patch.object(m, '_compute_covariance', return_value=(None, None)),
    ):
        driver_instance = mock_driver_cls.return_value
        driver_instance.fit.return_value = (fake_x, 0.5)
        driver_instance.clip = MagicMock()

        from bumps.parameter import Parameter as BumpsParameter

        bp1 = BumpsParameter(value=1.0, name='a')
        bp2 = BumpsParameter(value=2.0, name='b')
        bp1.value = 1.5
        bp2.value = 2.5

        res = m._run_solver(
            lambda v: np.array([0.0, 0.0]),
            bumps_params=[bp1, bp2],
        )

    assert isinstance(res, OptimizeResult)
    assert res.success is True
    np.testing.assert_array_almost_equal(res.x, [1.5, 2.5])


def test_run_solver_failure():
    from easydiffraction.analysis.minimizers.bumps import BumpsMinimizer

    m = BumpsMinimizer()

    fake_fitter = types.SimpleNamespace(id='lm')

    with (
        patch('easydiffraction.analysis.minimizers.bumps.FitDriver') as mock_driver_cls,
        patch('easydiffraction.analysis.minimizers.bumps.FitProblem'),
        patch('easydiffraction.analysis.minimizers.bumps.FITTERS', [fake_fitter]),
    ):
        driver_instance = mock_driver_cls.return_value
        driver_instance.fit.return_value = (None, None)
        driver_instance.clip = MagicMock()

        from bumps.parameter import Parameter as BumpsParameter

        bp = BumpsParameter(value=1.0, name='a')
        res = m._run_solver(
            lambda v: np.array([0.0]),
            bumps_params=[bp],
        )

    assert res.success is False
    assert res.status == -1


# -- _sync_result_to_parameters tests -----------------------------------------


def test_sync_result_to_parameters_with_optimize_result():
    from scipy.optimize import OptimizeResult

    from easydiffraction.analysis.minimizers.bumps import BumpsMinimizer

    m = BumpsMinimizer()
    params = [FakeParam('a', 1.0), FakeParam('b', 2.0)]
    result = OptimizeResult(
        x=np.array([10.0, 20.0]),
        dx=np.array([0.1, 0.2]),
        success=True,
    )
    m._sync_result_to_parameters(params, result)
    assert params[0].value == 10.0
    assert params[0].uncertainty == 0.1
    assert params[1].value == 20.0
    assert params[1].uncertainty == 0.2


def test_sync_result_to_parameters_without_dx():
    from scipy.optimize import OptimizeResult

    from easydiffraction.analysis.minimizers.bumps import BumpsMinimizer

    m = BumpsMinimizer()
    params = [FakeParam('a', 1.0)]
    result = OptimizeResult(x=np.array([5.0]), success=True)
    m._sync_result_to_parameters(params, result)
    assert params[0].value == 5.0
    assert params[0].uncertainty is None


def test_sync_result_to_parameters_converts_to_float():
    from scipy.optimize import OptimizeResult

    from easydiffraction.analysis.minimizers.bumps import BumpsMinimizer

    m = BumpsMinimizer()
    params = [FakeParam('a', 1.0)]
    result = OptimizeResult(
        x=np.array([np.float64(7.0)]),
        dx=np.array([np.float64(0.3)]),
        success=True,
    )
    m._sync_result_to_parameters(params, result)
    assert isinstance(params[0].value, float)
    assert isinstance(params[0].uncertainty, float)


def test_sync_with_raw_array():
    from easydiffraction.analysis.minimizers.bumps import BumpsMinimizer

    m = BumpsMinimizer()
    params = [FakeParam('a', 1.0)]
    m._sync_result_to_parameters(params, np.array([99.0]))
    assert params[0].value == 99.0
    assert params[0].uncertainty is None


# -- _check_success tests -----------------------------------------------------


def test_check_success_true():
    from scipy.optimize import OptimizeResult

    from easydiffraction.analysis.minimizers.bumps import BumpsMinimizer

    m = BumpsMinimizer()
    assert m._check_success(OptimizeResult(success=True)) is True


def test_check_success_false():
    from scipy.optimize import OptimizeResult

    from easydiffraction.analysis.minimizers.bumps import BumpsMinimizer

    m = BumpsMinimizer()
    assert m._check_success(OptimizeResult(success=False)) is False


def test_check_success_missing_attribute():
    from easydiffraction.analysis.minimizers.bumps import BumpsMinimizer

    m = BumpsMinimizer()
    assert m._check_success(object()) is False


# -- _compute_covariance tests ------------------------------------------------


def test_compute_covariance_basic():
    from bumps.parameter import Parameter as BumpsParameter

    from easydiffraction.analysis.minimizers.bumps import BumpsMinimizer
    from easydiffraction.analysis.minimizers.bumps import _EasyDiffractionFitness

    m = BumpsMinimizer()
    bp = BumpsParameter(value=2.0, name='a')
    # Linear objective: residual = value - target
    obj = lambda values: np.array([values[0] - 1.0] * 5)  # noqa: E731
    fitness = _EasyDiffractionFitness([bp], obj)
    fitness.nllf()

    cov, stderr = m._compute_covariance([bp], fitness)
    assert cov is not None
    assert stderr is not None
    assert cov.shape == (1, 1)
    assert len(stderr) == 1
    assert stderr[0] > 0


def test_compute_covariance_underdetermined():
    from bumps.parameter import Parameter as BumpsParameter

    from easydiffraction.analysis.minimizers.bumps import BumpsMinimizer
    from easydiffraction.analysis.minimizers.bumps import _EasyDiffractionFitness

    m = BumpsMinimizer()
    bp1 = BumpsParameter(value=1.0, name='a')
    bp2 = BumpsParameter(value=2.0, name='b')
    # Only 1 data point but 2 parameters → underdetermined
    obj = lambda values: np.array([values[0] + values[1]])  # noqa: E731
    fitness = _EasyDiffractionFitness([bp1, bp2], obj)
    fitness.nllf()

    cov, stderr = m._compute_covariance([bp1, bp2], fitness)
    assert cov is None
    assert stderr is None


# -- optimize result var_names and covar fields --------------------------------


def test_run_solver_result_has_var_names():
    from easydiffraction.analysis.minimizers.bumps import BumpsMinimizer

    m = BumpsMinimizer()

    fake_x = np.array([1.0])
    fake_fitter = types.SimpleNamespace(id='lm')

    with (
        patch('easydiffraction.analysis.minimizers.bumps.FitDriver') as mock_driver_cls,
        patch('easydiffraction.analysis.minimizers.bumps.FitProblem'),
        patch('easydiffraction.analysis.minimizers.bumps.FITTERS', [fake_fitter]),
        patch.object(m, '_compute_covariance', return_value=(None, None)),
    ):
        driver_instance = mock_driver_cls.return_value
        driver_instance.fit.return_value = (fake_x, 0.1)
        driver_instance.clip = MagicMock()

        from bumps.parameter import Parameter as BumpsParameter

        bp = BumpsParameter(value=1.0, name='my_param')
        res = m._run_solver(lambda v: np.array([0.0]), bumps_params=[bp])

    assert res.var_names == ['my_param']
