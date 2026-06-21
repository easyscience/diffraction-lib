# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

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


def _parameter(value):
    """Minimal category parameter stub."""
    return SimpleNamespace(value=value)


def _structure_stub(name_hm='P m -3 m'):
    """Minimal structure stub carrying only a space-group symbol."""
    return SimpleNamespace(
        space_group=SimpleNamespace(name_h_m=_parameter(name_hm)),
    )


def _cw_cfl_experiment_stub(
    x,
    zero,
    *,
    radiation_probe=None,
    wavelength_2=0.0,
    wavelength_2_to_1_ratio=0.0,
):
    """Minimal CWL experiment stub for CFL assembly."""
    from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
    from easydiffraction.datablocks.experiment.item.enums import RadiationProbeEnum

    if radiation_probe is None:
        radiation_probe = RadiationProbeEnum.NEUTRON

    return SimpleNamespace(
        name='offset test',
        experiment_type=SimpleNamespace(
            beam_mode=SimpleNamespace(value=BeamModeEnum.CONSTANT_WAVELENGTH),
            radiation_probe=SimpleNamespace(value=radiation_probe),
        ),
        data=SimpleNamespace(x=np.asarray(x, dtype=float)),
        instrument=SimpleNamespace(
            calib_twotheta_offset=_parameter(zero),
            setup_wavelength=_parameter(1.494),
            setup_wavelength_2=_parameter(wavelength_2),
            setup_wavelength_2_to_1_ratio=_parameter(wavelength_2_to_1_ratio),
        ),
        peak=SimpleNamespace(
            broad_gauss_u=_parameter(0.081547),
            broad_gauss_v=_parameter(-0.115345),
            broad_gauss_w=_parameter(0.121125),
            broad_lorentz_x=_parameter(0.0),
            broad_lorentz_y=_parameter(0.083038),
            asym_fcj_1=_parameter(0.0),
            asym_fcj_2=_parameter(0.0),
        ),
    )


def test_module_import():
    import easydiffraction.analysis.calculators.crysfml as MUT

    assert MUT.__name__ == 'easydiffraction.analysis.calculators.crysfml'


def test_crysfml_calculate_pattern_applies_absorption(monkeypatch):
    from easydiffraction.analysis.calculators.crysfml import CrysfmlCalculator
    from easydiffraction.analysis.corrections import absorption

    calc = CrysfmlCalculator()
    x = np.array([10.0, 90.0, 150.0])
    experiment = _absorption_experiment_stub(x, mu_r=0.7)
    raw = [100.0, 100.0, 100.0]
    monkeypatch.setattr(calc, '_crysfml_cfl', lambda s, e: [])
    monkeypatch.setattr(calc, '_calculate_adjusted_pattern', lambda d, e: list(raw))

    out = calc.calculate_pattern(_structure_stub(), experiment)

    expected = np.asarray(raw) * absorption.factor(x, experiment.absorption)
    assert np.allclose(out, expected)
    # The correction is non-trivial, so deleting the call site would fail.
    assert not np.allclose(out, raw)


def test_crysfml_calculate_pattern_applies_polarization(monkeypatch):
    from easydiffraction.analysis.calculators.crysfml import CrysfmlCalculator
    from easydiffraction.analysis.corrections import polarization
    from easydiffraction.datablocks.experiment.categories.instrument.cwl import CwlPdXrayInstrument

    calc = CrysfmlCalculator()
    x = np.array([0.0, 45.0, 90.0])
    instrument = CwlPdXrayInstrument()
    instrument.setup_polarization_coefficient = 0.5
    instrument.setup_monochromator_twotheta = 60.0
    experiment = SimpleNamespace(
        name='exp',
        instrument=instrument,
        data=SimpleNamespace(x=x),
    )
    raw = [100.0, 100.0, 100.0]
    monkeypatch.setattr(calc, '_crysfml_cfl', lambda s, e: [])
    monkeypatch.setattr(calc, '_calculate_adjusted_pattern', lambda d, e: list(raw))

    out = calc.calculate_pattern(_structure_stub(), experiment)

    expected = polarization.apply(raw, experiment)
    assert np.allclose(out, expected)
    assert not np.allclose(out, raw)


def test_crysfml_calculate_pattern_preserves_empty_no_data(monkeypatch):
    from easydiffraction.analysis.calculators.crysfml import CrysfmlCalculator

    calc = CrysfmlCalculator()
    experiment = _absorption_experiment_stub([10.0, 20.0], mu_r=0.7)
    monkeypatch.setattr(calc, '_crysfml_cfl', lambda s, e: [])

    def _raise(_dict, _experiment):
        msg = 'no calculated data'
        raise KeyError(msg)

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


def test_crysfml_cw_pattern_block_encodes_zero_in_grid():
    from easydiffraction.analysis.calculators.crysfml import CrysfmlCalculator

    calc = CrysfmlCalculator()
    experiment = _cw_cfl_experiment_stub([10.0, 11.0, 12.0], zero=0.5)

    block = calc._pattern_block(experiment)

    assert '  Zero_Sy  0.0  0.0  0.0' in block
    assert '  WDT  30' in block
    assert '  GEN_PATT  9.5  1  11.5' in block


def test_crysfml_cw_pattern_block_uses_xray_patt_type():
    from easydiffraction.analysis.calculators.crysfml import CrysfmlCalculator
    from easydiffraction.datablocks.experiment.item.enums import RadiationProbeEnum

    calc = CrysfmlCalculator()
    experiment = _cw_cfl_experiment_stub(
        [10.0, 11.0],
        zero=0.0,
        radiation_probe=RadiationProbeEnum.XRAY,
    )

    block = calc._pattern_block(experiment)

    assert '  Patt_Type  X-rays Powder CW' in block


def test_crysfml_cw_pattern_block_encodes_wavelength_doublet():
    from easydiffraction.analysis.calculators.crysfml import CrysfmlCalculator

    calc = CrysfmlCalculator()
    experiment = _cw_cfl_experiment_stub(
        [10.0, 11.0],
        zero=0.0,
        wavelength_2=1.5444,
        wavelength_2_to_1_ratio=0.5,
    )

    block = calc._pattern_block(experiment)

    assert '  LAMBDA  1.494  1.5444  0.5' in block


def test_crysfml_cw_pattern_block_rejects_ratio_without_wavelength_2():
    from easydiffraction.analysis.calculators.crysfml import CrysfmlCalculator

    calc = CrysfmlCalculator()
    experiment = _cw_cfl_experiment_stub(
        [10.0, 11.0],
        zero=0.0,
        wavelength_2_to_1_ratio=0.5,
    )

    with pytest.raises(ValueError, match='setup_wavelength_2'):
        calc._pattern_block(experiment)


def test_crysfml_cw_doublet_uses_single_wavelength_runs(monkeypatch):
    from easydiffraction.analysis.calculators.crysfml import CrysfmlCalculator

    calc = CrysfmlCalculator()
    experiment = _cw_cfl_experiment_stub(
        [10.0, 11.0],
        zero=0.0,
        wavelength_2=1.5444,
        wavelength_2_to_1_ratio=0.5,
    )
    cfl = calc._pattern_block(experiment)
    calls = []

    def _raw_pattern(lines):
        lambda_line = next(line for line in lines if line.lstrip().startswith('LAMBDA'))
        calls.append(lambda_line)
        if lambda_line == '  LAMBDA  1.494  1.494  0':
            return [10.0, 20.0]
        if lambda_line == '  LAMBDA  1.5444  1.5444  0':
            return [2.0, 4.0]
        return None

    monkeypatch.setattr(calc, '_calculate_raw_pattern', _raw_pattern)

    out = calc._calculate_adjusted_pattern(cfl, experiment)

    assert calls == ['  LAMBDA  1.494  1.494  0', '  LAMBDA  1.5444  1.5444  0']
    assert out == [11.0, 22.0]


def test_crysfml_adjust_pattern_length_truncates():
    from easydiffraction.analysis.calculators.crysfml import CrysfmlCalculator

    calc = CrysfmlCalculator()
    long = list(range(10))
    out = calc._adjust_pattern_length(long, target_length=4)
    assert out == [0, 1, 2, 3]


def test_crysfml_lattice_centering_points():
    from easydiffraction.analysis.calculators.crysfml import CrysfmlCalculator

    calc = CrysfmlCalculator()
    cases = {
        'P m -3 m': 1,
        'A m m 2': 2,
        'B b m m': 2,
        'C m c m': 2,
        'I a -3': 2,
        'R -3 m': 3,
        'F m -3 m': 4,
    }
    for name_hm, expected in cases.items():
        assert calc._lattice_centering_points(_structure_stub(name_hm)) == expected


def test_crysfml_centering_intensity_factor():
    from easydiffraction.analysis.calculators.crysfml import CrysfmlCalculator

    calc = CrysfmlCalculator()
    # factor = (n / (n - 1))**2 for centered lattices, 1.0 for primitive.
    assert calc._centering_intensity_factor(_structure_stub('P m -3 m')) == 1.0
    assert calc._centering_intensity_factor(_structure_stub('I a -3')) == 4.0
    assert calc._centering_intensity_factor(_structure_stub('R -3 m')) == pytest.approx(2.25)
    assert calc._centering_intensity_factor(_structure_stub('F m -3 m')) == pytest.approx(16 / 9)


def test_crysfml_unknown_centering_is_no_op():
    from easydiffraction.analysis.calculators.crysfml import CrysfmlCalculator

    calc = CrysfmlCalculator()
    assert calc._lattice_centering_points(_structure_stub('Z weird')) == 1
    assert calc._centering_intensity_factor(_structure_stub('Z weird')) == 1.0


def test_crysfml_apply_centering_intensity_correction_scales():
    from easydiffraction.analysis.calculators.crysfml import CrysfmlCalculator

    calc = CrysfmlCalculator()
    raw = [1.0, 2.0, 3.0]
    # I-centered -> x4
    out_i = calc._apply_centering_intensity_correction(list(raw), _structure_stub('I a -3'))
    assert out_i == [4.0, 8.0, 12.0]
    # Primitive -> unchanged (same list, no-op)
    out_p = calc._apply_centering_intensity_correction(list(raw), _structure_stub('P m -3 m'))
    assert out_p == raw
    # Empty pattern (e.g. unsupported TOF) -> unchanged, no structure access
    assert calc._apply_centering_intensity_correction([], None) == []
