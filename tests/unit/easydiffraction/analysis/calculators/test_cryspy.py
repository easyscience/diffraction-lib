# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from types import SimpleNamespace

import numpy as np
import pytest


def _cwl_experiment_stub():
    """Build a minimal CWL-powder experiment stub for dict-update tests."""
    from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
    from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum

    return SimpleNamespace(
        name='exp',
        experiment_type=SimpleNamespace(
            sample_form=SimpleNamespace(value=SampleFormEnum.POWDER),
            beam_mode=SimpleNamespace(value=BeamModeEnum.CONSTANT_WAVELENGTH),
        ),
        instrument=SimpleNamespace(
            calib_twotheta_offset=SimpleNamespace(value=0.1),
            setup_wavelength=SimpleNamespace(value=1.5),
            calib_sample_displacement=SimpleNamespace(value=0.05),
            calib_sample_transparency=SimpleNamespace(value=0.09),
        ),
        peak=SimpleNamespace(
            broad_gauss_u=SimpleNamespace(value=0.0),
            broad_gauss_v=SimpleNamespace(value=0.0),
            broad_gauss_w=SimpleNamespace(value=0.0),
            broad_lorentz_x=SimpleNamespace(value=0.0),
            broad_lorentz_y=SimpleNamespace(value=0.0),
        ),
    )


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


def test_cwl_cif_instrument_section_emits_sycos_sysin():
    import easydiffraction.analysis.calculators.cryspy as MUT
    from easydiffraction.datablocks.experiment.categories.instrument.cwl import CwlPdInstrument
    from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
    from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum

    expt_type = SimpleNamespace(
        beam_mode=SimpleNamespace(value=BeamModeEnum.CONSTANT_WAVELENGTH),
        sample_form=SimpleNamespace(value=SampleFormEnum.POWDER),
    )
    instrument = CwlPdInstrument()
    instrument.calib_sample_displacement = 0.05
    instrument.calib_sample_transparency = 0.09

    cif_lines: list[str] = []
    MUT._cif_instrument_section(cif_lines, expt_type, instrument)
    cif_text = '\n'.join(cif_lines)

    assert '_setup_offset_SyCos 0.05' in cif_text
    assert '_setup_offset_SySin 0.09' in cif_text


def test_update_experiment_in_cryspy_dict_sets_sycos_sysin():
    from easydiffraction.analysis.calculators.cryspy import CryspyCalculator

    experiment = _cwl_experiment_stub()
    cryspy_dict = {
        'pd_exp': {
            'offset_ttheta': [0.0],
            'wavelength': [0.0],
            'offset_sycos': [0.0],
            'offset_sysin': [0.0],
            'resolution_parameters': [0.0] * 5,
        }
    }

    CryspyCalculator._update_experiment_in_cryspy_dict(cryspy_dict, experiment)

    # SyCos/SySin are stored in plain degrees (cryspy converts internally).
    assert cryspy_dict['pd_exp']['offset_sycos'][0] == 0.05
    assert cryspy_dict['pd_exp']['offset_sysin'][0] == 0.09


def test_update_experiment_in_cryspy_dict_tolerates_missing_sycos_keys():
    # cryspy releases without PR #46 lack the offset keys; the update must
    # guard and not raise when they are absent.
    from easydiffraction.analysis.calculators.cryspy import CryspyCalculator

    experiment = _cwl_experiment_stub()
    cryspy_dict = {
        'pd_exp': {
            'offset_ttheta': [0.0],
            'wavelength': [0.0],
            'resolution_parameters': [0.0] * 5,
        }
    }

    CryspyCalculator._update_experiment_in_cryspy_dict(cryspy_dict, experiment)

    assert 'offset_sycos' not in cryspy_dict['pd_exp']


def test_update_structure_zeroes_biso_for_anisotropic_atoms():
    from easydiffraction.analysis.calculators.cryspy import CryspyCalculator
    from easydiffraction.datablocks.structure.item.base import Structure

    structure = Structure(name='test')
    structure.atom_sites.create(id='Si', type_symbol='Si', adp_type='Biso', adp_iso=0.5)
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
    structure.space_group.coord_system_code = 'h'
    structure.atom_sites.create(
        id='O',
        type_symbol='O',
        fract_x=0.20587714,
        fract_y=-0.20587714,
        fract_z=0.06271739,
        wyckoff_letter='h',
        adp_iso=0.5,
    )
    # The calculator reads the per-site multiplicity from the model, so
    # run the update flow to populate it via Wyckoff detection (R-3m 'h'
    # has multiplicity 18).
    structure._update_categories()
    assert structure.atom_sites['O'].multiplicity.value == 18

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
        experiment_type=SimpleNamespace(
            beam_mode=SimpleNamespace(value=BeamModeEnum.CONSTANT_WAVELENGTH)
        ),
    )

    records = calculator.last_powder_refln_records(structure, experiment, structure_id='phase-a')

    assert len(records) == 1
    assert records[0].structure_id == 'phase-a'
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
        experiment_type=SimpleNamespace(
            beam_mode=SimpleNamespace(value=BeamModeEnum.TIME_OF_FLIGHT)
        ),
    )

    records = calculator.last_powder_refln_records(structure, experiment, structure_id='phase-b')

    assert len(records) == 1
    assert records[0].structure_id == 'phase-b'
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
        experiment_type=SimpleNamespace(
            beam_mode=SimpleNamespace(value=BeamModeEnum.CONSTANT_WAVELENGTH)
        ),
    )

    records = calculator.last_powder_refln_records(structure, experiment, structure_id='phase-x')

    assert len(records) == 1
    assert records[0].structure_id == 'phase-x'
    assert records[0].two_theta == pytest.approx(60.0)
    assert records[0].d_spacing == pytest.approx(2.5)
    assert records[0].f_calc == pytest.approx(10.0)
    assert records[0].f_squared_calc == pytest.approx(100.0)


def _make_beta_structure():
    from easydiffraction.datablocks.structure.item.base import Structure

    structure = Structure(name='test')
    structure.space_group.name_h_m = 'P 1'
    structure.cell.length_a = 10.0
    structure.cell.length_b = 10.0
    structure.cell.length_c = 10.0
    structure.atom_sites.create(id='Fe', type_symbol='Fe', adp_iso=0.0)
    structure.atom_sites['Fe'].adp_type = 'beta'
    structure._sync_atom_site_aniso()
    aniso = structure.atom_site_aniso['Fe']
    aniso.adp_11 = 0.001
    aniso.adp_22 = 0.002
    aniso.adp_33 = 0.003
    aniso.adp_12 = -0.0004
    aniso.adp_13 = 0.0001
    aniso.adp_23 = -0.0002
    return structure


def test_update_aniso_beta_passes_stored_beta_through_unchanged():
    import math

    from easydiffraction.analysis.calculators.cryspy import CryspyCalculator

    structure = _make_beta_structure()
    cryspy_model_dict = {
        'unit_cell_parameters': [10.0, 10.0, 10.0, math.pi / 2, math.pi / 2, math.pi / 2],
        'atom_site_aniso_index': [0],
        'atom_beta': [[0.0], [0.0], [0.0], [0.0], [0.0], [0.0]],
    }

    CryspyCalculator._update_aniso_beta(cryspy_model_dict, structure)

    beta = cryspy_model_dict['atom_beta']
    assert beta[0][0] == pytest.approx(0.001)
    assert beta[1][0] == pytest.approx(0.002)
    assert beta[2][0] == pytest.approx(0.003)
    assert beta[3][0] == pytest.approx(-0.0004)
    assert beta[4][0] == pytest.approx(0.0001)
    assert beta[5][0] == pytest.approx(-0.0002)


def test_update_structure_zeroes_biso_for_beta_atoms():
    from easydiffraction.analysis.calculators.cryspy import CryspyCalculator

    structure = _make_beta_structure()
    cryspy_model_dict = {
        'unit_cell_parameters': [10.0, 10.0, 10.0, 0.0, 0.0, 0.0],
        'atom_fract_xyz': [[0.0], [0.0], [0.0]],
        'atom_occupancy': [1.0],
        'atom_b_iso': [123.0],
    }

    CryspyCalculator._update_structure_in_cryspy_dict(cryspy_model_dict, structure)

    assert cryspy_model_dict['atom_b_iso'][0] == 0.0


def test_temporarily_convert_to_u_notation_stashes_and_restores_beta():
    import math

    from easydiffraction.analysis.calculators.cryspy import CryspyCalculator
    from easydiffraction.datablocks.structure.categories.atom_sites.enums import AdpTypeEnum

    structure = _make_beta_structure()
    # cryspy parses only U/B aniso tags, so a beta atom is sent as Uani:
    # U_11 = beta_11 / (2*pi**2 * a*^2), with a* = 1/10 for this cell.
    expected_u11 = 0.001 / (2.0 * math.pi**2 * (1.0 / 10.0) ** 2)

    saved = CryspyCalculator._temporarily_convert_to_u_notation(structure)

    atom = structure.atom_sites['Fe']
    aniso = structure.atom_site_aniso['Fe']
    assert atom.adp_type.value == AdpTypeEnum.UANI.value
    assert aniso.adp_11.value == pytest.approx(expected_u11)
    assert '_atom_site_aniso.U_11' in aniso.adp_11._cif_handler.names

    CryspyCalculator._restore_from_u_notation(structure, saved)

    assert atom.adp_type.value == AdpTypeEnum.BETA.value
    assert aniso.adp_11.value == pytest.approx(0.001)
    assert aniso.adp_23.value == pytest.approx(-0.0002)
    assert '_atom_site_aniso.beta_11' in aniso.adp_11._cif_handler.names


def _bragg_powder_experiment(beam_mode):
    """Build a real Bragg powder experiment with one PO row."""
    from easydiffraction import ExperimentFactory

    experiment = ExperimentFactory.from_scratch(
        name='lbco',
        sample_form='powder',
        beam_mode=beam_mode,
        radiation_probe='neutron',
        scattering_type='bragg',
    )
    experiment.preferred_orientation.create(
        structure_id='lbco', march_r=0.5, index_h=0, index_k=0, index_l=1
    )
    return experiment


def test_cif_pref_orient_section_emits_for_constant_wavelength():
    import easydiffraction.analysis.calculators.cryspy as MUT

    experiment = _bragg_powder_experiment('constant wavelength')
    structure = SimpleNamespace(name='lbco')
    cif_lines: list[str] = []
    MUT._cif_pref_orient_section(cif_lines, experiment.experiment_type, experiment, structure)
    text = '\n'.join(cif_lines)

    assert '_texture_g_1' in text
    assert '_texture_label' in text
    # The row's user-facing March coefficient r=0.5 maps to cryspy
    # g_1 = 1/r = 2.0 (reciprocal convention).
    assert 'lbco 2.0' in text


def test_cif_pref_orient_section_skips_time_of_flight():
    # TOF is Deferred Work: no texture loop is emitted (the TOF cached
    # pass-through is not wired), so values cannot go stale.
    import easydiffraction.analysis.calculators.cryspy as MUT

    experiment = _bragg_powder_experiment('time-of-flight')
    structure = SimpleNamespace(name='lbco')
    cif_lines: list[str] = []
    MUT._cif_pref_orient_section(cif_lines, experiment.experiment_type, experiment, structure)

    assert not any('_texture_g_1' in line for line in cif_lines)


def test_update_texture_in_cryspy_dict_patches_g1_and_g2():
    import easydiffraction.analysis.calculators.cryspy as MUT

    experiment = _bragg_powder_experiment('constant wavelength')
    experiment.preferred_orientation['lbco'].march_r = 0.6
    experiment.preferred_orientation['lbco'].march_random_fract = 0.2

    cryspy_expt_dict = {
        'texture_name': ['lbco'],
        'texture_g1': [1.0],
        'texture_g2': [0.0],
    }
    MUT._update_texture_in_cryspy_dict(cryspy_expt_dict, experiment)

    # r maps to cryspy g_1 = 1/r (reciprocal); fraction maps to g_2.
    assert cryspy_expt_dict['texture_g1'][0] == pytest.approx(1.0 / 0.6)
    assert cryspy_expt_dict['texture_g2'][0] == 0.2


def test_update_texture_in_cryspy_dict_noop_without_texture_keys():
    import easydiffraction.analysis.calculators.cryspy as MUT

    experiment = _bragg_powder_experiment('constant wavelength')
    cryspy_expt_dict = {'wavelength': [1.5]}
    MUT._update_texture_in_cryspy_dict(cryspy_expt_dict, experiment)

    assert 'texture_g1' not in cryspy_expt_dict


def test_invalidate_stale_cache_drops_dict_on_pref_orient_axis_change():
    from easydiffraction.analysis.calculators.cryspy import CryspyCalculator

    experiment = _bragg_powder_experiment('constant wavelength')
    calc = CryspyCalculator()
    combined_name = 'lbco_lbco'

    # First pass records the peak/pref-orient signatures (and drops the
    # cache because nothing was recorded yet); re-populate afterwards.
    calc._invalidate_stale_cache(combined_name, experiment, None)
    calc._cryspy_dicts[combined_name] = {'sentinel': True}

    # No change -> cache survives.
    calc._invalidate_stale_cache(combined_name, experiment, None)
    assert combined_name in calc._cryspy_dicts

    # Value-only edit must NOT invalidate.
    experiment.preferred_orientation['lbco'].march_r = 2.0
    calc._invalidate_stale_cache(combined_name, experiment, None)
    assert combined_name in calc._cryspy_dicts

    # Direction edit changes the signature and must drop the cache.
    experiment.preferred_orientation['lbco'].index_l = 0
    experiment.preferred_orientation['lbco'].index_h = 1
    calc._invalidate_stale_cache(combined_name, experiment, None)
    assert combined_name not in calc._cryspy_dicts


def test_relabel_cif_tags_for_cryspy_maps_edifa_tags_to_legacy():
    """Edifa tags map to the legacy IUCr spellings cryspy needs."""
    from easydiffraction.analysis.calculators.cryspy import CryspyCalculator

    cif = (
        '_space_group.name_h_m "P m -3 m"\n'
        '_space_group.coord_system_code 1\n'
        'loop_\n_atom_site.id\n_atom_site.adp_iso\nSi 0.4\n'
        'loop_\n_atom_site_aniso.id\n_atom_site_aniso.adp_11\nSi 0.01\n'
    )

    out = CryspyCalculator._relabel_cif_tags_for_cryspy(cif)

    assert '_space_group.name_H-M_alt' in out
    assert '_space_group.IT_coordinate_system_code' in out
    assert '_atom_site.label' in out
    assert '_atom_site.U_iso_or_equiv' in out
    assert '_atom_site_aniso.label' in out
    assert '_atom_site_aniso.U_11' in out
    # The Edifa spellings are fully removed.
    assert '_atom_site.id\n' not in out
    assert '_atom_site.adp_iso' not in out
    assert '_space_group.name_h_m' not in out
