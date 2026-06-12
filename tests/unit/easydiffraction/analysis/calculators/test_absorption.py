# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

import numpy as np
import pytest


class _FakeData:
    def __init__(self, x):
        self.x = x


class _FakeExperiment:
    """Minimal stand-in exposing ``absorption`` and ``data.x``."""

    def __init__(self, absorption, x):
        self.absorption = absorption
        self.data = _FakeData(x)


def _none():
    from easydiffraction.datablocks.experiment.categories.absorption.none import NoAbsorption

    return NoAbsorption()


def _hewat(mu_r):
    from easydiffraction.datablocks.experiment.categories.absorption.cylinder_hewat import (
        CylinderHewatAbsorption,
    )

    absorption = CylinderHewatAbsorption()
    absorption.mu_r = mu_r
    return absorption


def test_module_import():
    import easydiffraction.analysis.calculators.absorption as MUT

    assert MUT.__name__.endswith('calculators.absorption')


def test_factor_none_is_unity():
    from easydiffraction.analysis.calculators import absorption

    two_theta = np.array([10.0, 50.0, 120.0])
    result = absorption.factor(two_theta, _none())
    assert np.allclose(result, 1.0)


def test_factor_hewat_matches_fullprof_to_four_decimals():
    # A(2theta=90, muR=0.7): theta=45deg, sin^2=0.5
    #   exp(-(1.7133-0.0368*0.5)*0.7 + (0.0927+0.375*0.5)*0.49) ~ 0.35024
    from easydiffraction.analysis.calculators import absorption

    result = absorption.factor(np.array([90.0]), _hewat(0.7))
    assert result[0] == pytest.approx(0.35024, abs=1e-4)


def test_factor_hewat_is_unity_at_zero_mu_r():
    from easydiffraction.analysis.calculators import absorption

    result = absorption.factor(np.array([10.0, 90.0, 150.0]), _hewat(0.0))
    assert np.allclose(result, 1.0)


def test_factor_hewat_attenuates_low_angle_more():
    # The cylindrical correction is monotonically increasing in 2theta.
    from easydiffraction.analysis.calculators import absorption

    result = absorption.factor(np.array([10.0, 90.0, 160.0]), _hewat(0.7))
    assert result[0] < result[1] < result[2]


def test_factor_warns_once_for_large_mu_r(monkeypatch):
    from easydiffraction.analysis.calculators import absorption

    monkeypatch.setattr(absorption, '_WARNED_MU_R', set())
    calls = []
    monkeypatch.setattr(absorption.log, 'warning', lambda *a, **k: calls.append(a))

    big = _hewat(2.0)  # above HEWAT_MAX_VALIDATED_MU_R
    absorption.factor(np.array([90.0]), big)
    absorption.factor(np.array([90.0]), big)  # same value: no second warning
    assert len(calls) == 1


def test_apply_multiplies_pattern():
    from easydiffraction.analysis.calculators import absorption

    x = np.array([10.0, 90.0, 150.0])
    y = np.array([100.0, 100.0, 100.0])
    expected = y * absorption.factor(x, _hewat(0.7))
    experiment = _FakeExperiment(_hewat(0.7), x)
    assert np.allclose(absorption.apply(y, experiment), expected)


def test_apply_returns_unchanged_without_absorption():
    from easydiffraction.analysis.calculators import absorption

    class _NoAttr:
        data = _FakeData(np.array([10.0, 20.0]))

    y = [1.0, 2.0]
    assert absorption.apply(y, _NoAttr()) is y


def test_apply_returns_unchanged_for_empty_pattern():
    from easydiffraction.analysis.calculators import absorption

    experiment = _FakeExperiment(_hewat(0.7), np.array([10.0, 20.0]))
    y = []
    assert absorption.apply(y, experiment) is y


def test_apply_returns_unchanged_on_length_mismatch():
    from easydiffraction.analysis.calculators import absorption

    experiment = _FakeExperiment(_hewat(0.7), np.array([10.0, 20.0, 30.0]))
    y = np.array([1.0, 2.0])  # shorter than the 2-theta grid
    assert absorption.apply(y, experiment) is y
