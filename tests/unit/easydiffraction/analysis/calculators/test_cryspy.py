# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from types import SimpleNamespace


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
    import numpy as np

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
