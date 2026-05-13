# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from types import SimpleNamespace

import numpy as np
import pytest


def test_module_import():
    import easydiffraction.analysis.calculators.cryspy as MUT

    assert MUT.__name__ == 'easydiffraction.analysis.calculators.cryspy'


def test_cryspy_calculator_engine_flag_and_converters():
    # These tests avoid requiring real cryspy by not invoking heavy paths
    from easydiffraction.analysis.calculators.cryspy import CryspyCalculator

    calc = CryspyCalculator()
    # engine_imported is boolean (may be False if cryspy not installed)
    assert isinstance(calc.engine_imported, bool)

    # Converters should just delegate/format without external deps
    class DummySample:
        atom_sites = []

        @property
        def as_cif(self):
            return 'data_x'

    # _convert_structure_to_cryspy_cif returns input as_cif
    assert calc._convert_structure_to_cryspy_cif(DummySample()) == 'data_x'


def test_tof_pseudo_voigt_cif_section_uses_non_convoluted_peak_shape():
    import easydiffraction.analysis.calculators.cryspy as MUT
    from easydiffraction.datablocks.experiment.categories.peak.tof import TofPseudoVoigt
    from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
    from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum

    expt_type = SimpleNamespace(
        beam_mode=SimpleNamespace(value=BeamModeEnum.TIME_OF_FLIGHT),
        sample_form=SimpleNamespace(value=SampleFormEnum.POWDER),
    )
    peak = TofPseudoVoigt()
    peak.broad_gauss_sigma_0 = 1.0
    peak.broad_gauss_sigma_1 = 2.0
    peak.broad_gauss_sigma_2 = 3.0
    peak.broad_lorentz_gamma_0 = 4.0
    peak.broad_lorentz_gamma_1 = 5.0
    peak.broad_lorentz_gamma_2 = 6.0

    cif_lines: list[str] = []
    MUT._cif_peak_section(cif_lines, expt_type, peak)
    cif_text = '\n'.join(cif_lines)

    assert '_tof_profile_peak_shape non-conv-pseudo-Voigt' in cif_text
    assert '_tof_profile_gamma0 4.0' in cif_text
    assert '_tof_profile_gamma1 5.0' in cif_text
    assert '_tof_profile_gamma2 6.0' in cif_text
    assert '_tof_profile_alpha0' not in cif_text
    assert '_tof_profile_beta0' not in cif_text


def test_update_structure_zeroes_biso_for_anisotropic_atoms():
    from easydiffraction.analysis.calculators.cryspy import CryspyCalculator
    from easydiffraction.datablocks.structure.item.base import Structure

    structure = Structure(name='test')
    structure.atom_sites.create(label='Si', type_symbol='Si', adp_type='Biso', adp_iso=0.5)
    structure.atom_sites['Si'].adp_type = 'Bani'

    cryspy_model_dict = {
        'unit_cell_parameters': [0.0] * 6,
        'atom_fract_xyz': [[0.0], [0.0], [0.0]],
        'atom_occupancy': [0.0],
        'atom_b_iso': [123.0],
    }

    CryspyCalculator._update_structure_in_cryspy_dict(cryspy_model_dict, structure)

    assert cryspy_model_dict['atom_b_iso'][0] == 0.0


def test_update_structure_restores_wyckoff_multiplicity_after_coordinate_wrapping():
    pytest.importorskip('cryspy')

    from easydiffraction.analysis.calculators.cryspy import CryspyCalculator
    from easydiffraction.datablocks.structure.item.base import Structure

    structure = Structure(name='hs')
    structure.space_group.name_h_m = 'R -3 m'
    structure.space_group.it_coordinate_system_code = 'h'
    structure.atom_sites.create(
        label='O',
        type_symbol='O',
        fract_x=0.20587714,
        fract_y=-0.20587714,
        fract_z=0.06271739,
        wyckoff_letter='h',
        adp_iso=0.5,
    )

    cryspy_model_dict = {
        'unit_cell_parameters': [6.86, 6.86, 14.14, np.pi / 2, np.pi / 2, 2 * np.pi / 3],
        'atom_fract_xyz': np.array([[0.20587714], [0.79412286], [0.06271739]]),
        'atom_occupancy': np.array([1.0]),
        'atom_multiplicity': np.array([36]),
        'atom_b_iso': np.array([0.5]),
    }

    CryspyCalculator._update_structure_in_cryspy_dict(cryspy_model_dict, structure)

    assert cryspy_model_dict['atom_fract_xyz'][1][0] == -0.20587714
    assert cryspy_model_dict['atom_multiplicity'][0] == 18


def test_last_powder_refln_records_converts_cwl_two_theta_to_degrees():
    from easydiffraction.analysis.calculators.cryspy import CryspyCalculator
    from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum

    calculator = CryspyCalculator()
    calculator._last_powder_phase_blocks = {
        'phase_exp': {
            'index_hkl': np.array([[1], [0], [1]]),
            'sthovl': np.array([0.25]),
            'ttheta_hkl': np.array([np.pi / 2]),
            'f_nucl': np.array([-3.0 + 4.0j]),
        }
    }
    structure = SimpleNamespace(name='phase')
    experiment = SimpleNamespace(
        name='exp',
        type=SimpleNamespace(beam_mode=SimpleNamespace(value=BeamModeEnum.CONSTANT_WAVELENGTH)),
    )

    records = calculator.last_powder_refln_records(structure, experiment, phase_id='phase-a')

    assert len(records) == 1
    assert records[0].phase_id == 'phase-a'
    assert records[0].two_theta == pytest.approx(90.0)
    assert records[0].d_spacing == pytest.approx(2.0)
    assert records[0].f_calc == pytest.approx(5.0)
    assert records[0].f_squared_calc == pytest.approx(25.0)


def test_last_powder_refln_records_reads_tof_time_and_d_spacing():
    from easydiffraction.analysis.calculators.cryspy import CryspyCalculator
    from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum

    calculator = CryspyCalculator()
    calculator._last_powder_phase_blocks = {
        'phase_exp': {
            'index_hkl': np.array([[2], [1], [0]]),
            'sthovl': np.array([0.1]),
            'd_hkl': np.array([3.21]),
            'time_hkl': np.array([1234.0]),
            'f_nucl': np.array([6.0 + 0.0j]),
        }
    }
    structure = SimpleNamespace(name='phase')
    experiment = SimpleNamespace(
        name='exp',
        type=SimpleNamespace(beam_mode=SimpleNamespace(value=BeamModeEnum.TIME_OF_FLIGHT)),
    )

    records = calculator.last_powder_refln_records(structure, experiment, phase_id='phase-b')

    assert len(records) == 1
    assert records[0].phase_id == 'phase-b'
    assert records[0].time_of_flight == pytest.approx(1234.0)
    assert records[0].d_spacing == pytest.approx(3.21)
    assert records[0].f_calc == pytest.approx(6.0)
    assert records[0].f_squared_calc == pytest.approx(36.0)


def test_last_powder_refln_records_reads_xray_charge_structure_factor():
    from easydiffraction.analysis.calculators.cryspy import CryspyCalculator
    from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum

    calculator = CryspyCalculator()
    calculator._last_powder_phase_blocks = {
        'phase_exp': {
            'index_hkl': np.array([[1], [1], [1]]),
            'sthovl': np.array([0.2]),
            'ttheta_hkl': np.array([np.pi / 3]),
            'f_charge': np.array([8.0 - 6.0j]),
        }
    }
    structure = SimpleNamespace(name='phase')
    experiment = SimpleNamespace(
        name='exp',
        type=SimpleNamespace(beam_mode=SimpleNamespace(value=BeamModeEnum.CONSTANT_WAVELENGTH)),
    )

    records = calculator.last_powder_refln_records(structure, experiment, phase_id='phase-x')

    assert len(records) == 1
    assert records[0].phase_id == 'phase-x'
    assert records[0].two_theta == pytest.approx(60.0)
    assert records[0].d_spacing == pytest.approx(2.5)
    assert records[0].f_calc == pytest.approx(10.0)
    assert records[0].f_squared_calc == pytest.approx(100.0)
