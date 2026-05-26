# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for the IUCr journal-submission CIF writer."""

from __future__ import annotations

from collections import UserDict
from types import SimpleNamespace

from easydiffraction.io.cif.handler import CifHandler


class _Descriptor:
    def __init__(self, value, tag='_x.value', iucr_name=None):
        self.value = value
        self._cif_handler = CifHandler(names=[tag], iucr_name=iucr_name)


class _Collection(UserDict):
    @property
    def names(self):
        return list(self.data)


def _collection(*items):
    return _Collection({item.name: item for item in items})


def _descriptor(value, tag='_x.value', iucr_name=None):
    return _Descriptor(value, tag=tag, iucr_name=iucr_name)


def _experiment_type(*, sample_form, beam_mode='constant wavelength'):
    return SimpleNamespace(
        sample_form=_descriptor(
            sample_form,
            '_expt_type.sample_form',
            '_easydiffraction_experiment_type.sample_form',
        ),
        beam_mode=_descriptor(
            beam_mode,
            '_expt_type.beam_mode',
            '_easydiffraction_experiment_type.beam_mode',
        ),
        radiation_probe=_descriptor(
            'neutron',
            '_expt_type.radiation_probe',
            '_easydiffraction_experiment_type.radiation_probe',
        ),
        scattering_type=_descriptor(
            'bragg',
            '_expt_type.scattering_type',
            '_easydiffraction_experiment_type.scattering_type',
        ),
    )


def _fit_result():
    from easydiffraction.analysis.categories.fit_result.lsq import (
        LeastSquaresFitResult,
    )

    fit_result = LeastSquaresFitResult()
    fit_result._set_n_parameters(4)
    fit_result._set_r_factor_all(0.12)
    fit_result._set_wr_factor_all(0.13)
    fit_result._set_r_factor_gt(0.08)
    fit_result._set_wr_factor_gt(0.09)
    fit_result._set_number_reflns_total(8)
    fit_result._set_number_reflns_gt(6)
    fit_result._set_threshold_expression('I > 3u(I)')
    fit_result._set_prof_r_factor(0.21)
    fit_result._set_prof_wr_factor(0.22)
    fit_result._set_prof_wr_expected(0.23)
    fit_result._set_profile_function('pseudo-Voigt')
    fit_result._set_background_function('Chebyshev')
    return fit_result


def _structure(name='phase1'):
    from easydiffraction.datablocks.structure.item.base import Structure

    structure = Structure(name=name)
    structure.cell.length_a = 5.43
    structure.cell.length_b = 5.43
    structure.cell.length_c = 5.43
    structure.atom_sites.create(
        label='Si1',
        type_symbol='Si',
        fract_x=0.0,
        fract_y=0.0,
        fract_z=0.0,
        adp_type='Biso',
        adp_iso=0.4,
    )
    return structure


def _project(name, tmp_path, structures, experiments):
    return SimpleNamespace(
        name=name,
        info=SimpleNamespace(path=tmp_path),
        structures=structures,
        experiments=experiments,
        analysis=SimpleNamespace(
            minimizer=SimpleNamespace(type=_descriptor('lmfit')),
            fit_result=_fit_result(),
        ),
    )


def _single_crystal_experiment(name='sc1'):
    return SimpleNamespace(
        name=name,
        type=_experiment_type(sample_form='single crystal'),
        linked_crystal=SimpleNamespace(
            id=_descriptor(
                'phase1',
                '_sc_crystal_block.id',
                '_easydiffraction_sc_crystal_block.id',
            ),
            scale=_descriptor(
                1.0,
                '_sc_crystal_block.scale',
                '_easydiffraction_sc_crystal_block.scale',
            ),
        ),
        diffrn=SimpleNamespace(
            ambient_temperature=_descriptor(295.0),
            ambient_pressure=_descriptor(101.3),
            ambient_magnetic_field=_descriptor(
                None,
                '_diffrn.ambient_magnetic_field',
                '_easydiffraction_diffrn.ambient_magnetic_field',
            ),
            ambient_electric_field=_descriptor(
                None,
                '_diffrn.ambient_electric_field',
                '_easydiffraction_diffrn.ambient_electric_field',
            ),
        ),
        instrument=SimpleNamespace(setup_wavelength=_descriptor(1.5406)),
        calculator=SimpleNamespace(
            type=_descriptor(
                'cryspy',
                '_calculator.type',
                '_easydiffraction_calculator.type',
            )
        ),
        extinction=None,
        refln=[
            SimpleNamespace(
                index_h=_descriptor(1),
                index_k=_descriptor(0),
                index_l=_descriptor(0),
                intensity_meas=_descriptor(100.0),
                intensity_calc=_descriptor(98.0),
                intensity_meas_su=_descriptor(2.0),
            )
        ],
    )


def _linked_phase():
    return SimpleNamespace(
        id=_descriptor('phase1'),
        scale=_descriptor(1.0),
    )


def _powder_experiment(name, *, beam_mode='constant wavelength'):
    point = (
        SimpleNamespace(
            two_theta=_descriptor(10.0),
            intensity_meas=_descriptor(100.0),
            intensity_calc=_descriptor(98.0),
            intensity_bkg=_descriptor(4.0),
            intensity_meas_su=_descriptor(5.0),
        )
        if beam_mode == 'constant wavelength'
        else SimpleNamespace(
            time_of_flight=_descriptor(2500.0),
            intensity_meas=_descriptor(100.0),
            intensity_calc=_descriptor(98.0),
            intensity_bkg=_descriptor(4.0),
            intensity_meas_su=_descriptor(5.0),
        )
    )
    return SimpleNamespace(
        name=name,
        type=_experiment_type(sample_form='powder', beam_mode=beam_mode),
        linked_phases=[_linked_phase()],
        diffrn=SimpleNamespace(
            ambient_temperature=_descriptor(295.0),
            ambient_pressure=_descriptor(101.3),
        ),
        instrument=SimpleNamespace(
            setup_wavelength=_descriptor(1.5406 if beam_mode == 'constant wavelength' else None),
            calib_d_to_tof_offset=_descriptor(1.0),
            calib_d_to_tof_linear=_descriptor(2.0),
            calib_d_to_tof_quad=_descriptor(3.0),
            calib_d_to_tof_recip=_descriptor(4.0),
        ),
        calculator=SimpleNamespace(
            type=_descriptor(
                'cryspy',
                '_calculator.type',
                '_easydiffraction_calculator.type',
            )
        ),
        peak=SimpleNamespace(
            type=_descriptor('pseudo-Voigt', '_peak.type', '_easydiffraction_peak.type')
        ),
        background=SimpleNamespace(
            type=_descriptor(
                'chebyshev',
                '_background.type',
                '_easydiffraction_background.type',
            )
        ),
        excluded_regions=[
            SimpleNamespace(start=_descriptor(15.0), end=_descriptor(17.0)),
        ],
        data=[point],
        refln=[
            SimpleNamespace(
                index_h=_descriptor(1),
                index_k=_descriptor(0),
                index_l=_descriptor(0),
                f_squared_calc=_descriptor(25.0),
                phase_id=_descriptor('phase1'),
                d_spacing=_descriptor(2.5),
            )
        ],
    )


def test_write_iucr_cif_writes_global_block(tmp_path):
    from easydiffraction.io.cif.iucr_writer import write_iucr_cif

    project = _project('demo', tmp_path, _Collection(), _Collection())

    report_path = write_iucr_cif(project)
    text = report_path.read_text(encoding='utf-8')

    assert report_path == tmp_path / 'reports' / 'demo.cif'
    assert text.startswith('data_global\n')
    assert '_audit.creation_method' in text
    assert '_computing.structure_refinement' in text
    assert '_easydiffraction_software.framework' in text
    assert '_easydiffraction_software.minimizer' in text


def test_write_iucr_cif_emits_single_crystal_block(tmp_path):
    from easydiffraction.io.cif.iucr_writer import write_iucr_cif

    project = _project(
        'sc_project',
        tmp_path,
        _collection(_structure()),
        _collection(_single_crystal_experiment()),
    )

    text = write_iucr_cif(project).read_text(encoding='utf-8')

    assert text.index('data_global') < text.index('data_phase1')
    assert '_diffrn_radiation_wavelength.value' in text
    assert '_atom_site.B_iso_or_equiv' in text
    assert '_atom_site.U_iso_or_equiv' not in text
    assert '_refine_ls.R_factor_all' in text
    assert '_reflns.number_total' in text
    assert '_easydiffraction_calculator.type' in text


def test_write_iucr_cif_emits_powder_cwl_blocks(tmp_path):
    from easydiffraction.io.cif.iucr_writer import write_iucr_cif

    project = _project(
        'powder',
        tmp_path,
        _collection(_structure()),
        _collection(_powder_experiment('cwl')),
    )

    text = write_iucr_cif(project).read_text(encoding='utf-8')

    assert 'data_powder_overall' in text
    assert 'data_powder_phase_1' in text
    assert 'data_powder_pwd_1' in text
    assert '_pd_meas.2theta_scan' in text
    assert '_pd_meas.time_of_flight' not in text
    assert '_pd_proc.info_excluded_regions' in text
    assert '_easydiffraction_background.type' in text


def test_write_iucr_cif_emits_joint_tof_pattern_blocks(tmp_path):
    from easydiffraction.io.cif.iucr_writer import write_iucr_cif

    project = _project(
        'joint',
        tmp_path,
        _collection(_structure()),
        _collection(
            _powder_experiment('tof1', beam_mode='time-of-flight'),
            _powder_experiment('tof2', beam_mode='time-of-flight'),
        ),
    )

    text = write_iucr_cif(project).read_text(encoding='utf-8')

    assert 'data_joint_pwd_1' in text
    assert 'data_joint_pwd_2' in text
    assert '_pd_meas.time_of_flight' in text
    assert '_pd_calib_d_to_tof.power' in text
    assert 'recip' in text
    assert '-1' in text
