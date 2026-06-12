# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from types import SimpleNamespace

import numpy as np
import pytest


def _absorption_experiment_stub(x, mu_r):
    """Minimal CWL experiment stub carrying a cylindrical absorption."""
    from easydiffraction.datablocks.experiment.categories.absorption.cylinder_hewat import (
        CylinderHewatAbsorption,
    )
    from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum

    absorption = CylinderHewatAbsorption()
    absorption.mu_r = mu_r
    return SimpleNamespace(
        name='exp',
        type=SimpleNamespace(beam_mode=SimpleNamespace(value=BeamModeEnum.CONSTANT_WAVELENGTH)),
        absorption=absorption,
        data=SimpleNamespace(x=np.asarray(x, dtype=float)),
    )


def test_module_import():
    import easydiffraction.analysis.calculators.crysfml as MUT

    assert MUT.__name__ == 'easydiffraction.analysis.calculators.crysfml'


def test_crysfml_calculate_pattern_applies_absorption(monkeypatch):
    from easydiffraction.analysis.calculators import absorption
    from easydiffraction.analysis.calculators.crysfml import CrysfmlCalculator

    calc = CrysfmlCalculator()
    x = np.array([10.0, 90.0, 150.0])
    experiment = _absorption_experiment_stub(x, mu_r=0.7)
    raw = [100.0, 100.0, 100.0]
    monkeypatch.setattr(calc, '_crysfml_dict', lambda s, e: {})
    monkeypatch.setattr(calc, '_calculate_adjusted_pattern', lambda d, e: list(raw))

    out = calc.calculate_pattern(None, experiment)

    expected = np.asarray(raw) * absorption.factor(x, experiment.absorption)
    assert np.allclose(out, expected)
    # The correction is non-trivial, so deleting the call site would fail.
    assert not np.allclose(out, raw)


def test_crysfml_calculate_pattern_preserves_empty_no_data(monkeypatch):
    from easydiffraction.analysis.calculators.crysfml import CrysfmlCalculator

    calc = CrysfmlCalculator()
    experiment = _absorption_experiment_stub([10.0, 20.0], mu_r=0.7)
    monkeypatch.setattr(calc, '_crysfml_dict', lambda s, e: {})

    def _raise(_dict, _experiment):
        raise KeyError('no calculated data')

    monkeypatch.setattr(calc, '_calculate_adjusted_pattern', _raise)

    out = calc.calculate_pattern(None, experiment)
    assert np.asarray(out).size == 0


def test_crysfml_engine_flag_and_structure_factors_raises():
    from easydiffraction.analysis.calculators.crysfml import CrysfmlCalculator

    calc = CrysfmlCalculator()
    # engine_imported is a boolean flag; it may be False in our env
    assert isinstance(calc.engine_imported, bool)
    with pytest.raises(NotImplementedError):
        calc.calculate_structure_factors(structures=None, experiments=None)


def test_crysfml_adjust_pattern_length_truncates():
    from easydiffraction.analysis.calculators.crysfml import CrysfmlCalculator

    calc = CrysfmlCalculator()
    long = list(range(10))
    out = calc._adjust_pattern_length(long, target_length=4)
    assert out == [0, 1, 2, 3]
