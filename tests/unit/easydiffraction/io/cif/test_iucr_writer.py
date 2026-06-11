# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for the IUCr journal-submission CIF writer."""

from __future__ import annotations

from collections import UserDict
from types import SimpleNamespace

from easydiffraction.io.cif.handler import CifHandler


class _Descriptor:
    def __init__(self, value, tag='_x.value', iucr_name=None):
        self.name = tag.rsplit('.', maxsplit=1)[-1]
        self.value = value
        self._cif_handler = CifHandler(names=[tag], iucr_name=iucr_name)


class _SwitchableCategory:
    def __init__(
        self,
        value,
        tag,
        iucr_name,
        *,
        descriptor_source='parameters',
    ):
        self._type = _descriptor(value, tag, iucr_name)
        self._descriptor_source = descriptor_source

    @property
    def type(self):
        return self._type.value

    @property
    def parameters(self):
        if self._descriptor_source == 'parameters':
            return [self._type]
        return []

    @property
    def scalar_descriptors(self):
        if self._descriptor_source == 'scalar_descriptors':
            return [self._type]
        return []


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
    from easydiffraction.analysis.categories.fit_result.lsq import LeastSquaresFitResult

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
        calculator=_SwitchableCategory(
            'cryspy',
            '_calculator.type',
            '_easydiffraction_calculator.type',
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
        calculator=_SwitchableCategory(
            'cryspy',
            '_calculator.type',
            '_easydiffraction_calculator.type',
        ),
        peak=_SwitchableCategory(
            'pseudo-Voigt',
            '_peak.type',
            '_easydiffraction_peak.type',
            descriptor_source='scalar_descriptors',
        ),
        background=_SwitchableCategory(
            'chebyshev',
            '_background.type',
            '_easydiffraction_background.type',
            descriptor_source='scalar_descriptors',
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
    assert '_journal.' not in text
    assert '_publ_' not in text


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


def test_write_iucr_cif_omits_space_group_wyckoff_loop(tmp_path):
    from easydiffraction.io.cif.iucr_writer import write_iucr_cif

    # The derived Wyckoff table is code-only; reports never emit it, even
    # for a space group whose table is non-empty.
    structure = _structure()
    structure.space_group.name_h_m = 'P m -3 m'
    structure._update_categories()
    assert len(structure.space_group_wyckoff) > 0

    project = _project(
        'wyckoff_omitted',
        tmp_path,
        _collection(structure),
        _collection(_single_crystal_experiment()),
    )

    text = write_iucr_cif(project).read_text(encoding='utf-8')

    assert '_space_group_Wyckoff' not in text


def test_write_iucr_cif_emits_powder_cwl_blocks(tmp_path):
    from easydiffraction.io.cif.iucr_writer import write_iucr_cif

    project = _project(
        'powder',
        tmp_path,
        _collection(_structure()),
        _collection(_powder_experiment('cwl')),
    )

    text = write_iucr_cif(project).read_text(encoding='utf-8')

    assert 'data_overall' in text
    assert 'data_phase1' in text
    assert 'data_cwl' in text
    assert '_pd_block_id                           phase1' in text
    assert '_pd_block_diffractogram_id             cwl' in text
    assert '|phase1|' not in text
    assert '|cwl|' not in text
    assert '_pd_meas.2theta_scan' in text
    assert '_pd_meas.time_of_flight' not in text
    assert '_pd_refln.phase_id' in text
    assert '_refln.phase_calc' not in text
    assert '_pd_proc.info_excluded_regions' in text
    assert '_easydiffraction_background.type' in text
    assert '_pd_meas.info_author_' not in text


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

    assert 'data_tof1' in text
    assert 'data_tof2' in text
    assert '\n_pd_block_diffractogram_id\n  tof1\n  tof2\n' in text
    assert '_pd_meas.time_of_flight' in text
    assert '_pd_calib_d_to_tof.power' in text
    assert 'recip' in text
    assert '-1' in text


def test_write_iucr_cif_keeps_powder_block_names_unique(tmp_path):
    from easydiffraction.io.cif.iucr_writer import write_iucr_cif

    project = _project(
        'demo',
        tmp_path,
        _collection(_structure(name='overall')),
        _collection(_powder_experiment('overall')),
    )

    text = write_iucr_cif(project).read_text(encoding='utf-8')

    assert 'data_overall' in text
    assert 'data_overall_2' in text
    assert 'data_overall_3' in text


def test_write_iucr_cif_keeps_mixed_topology_block_names_unique(tmp_path):
    from easydiffraction.io.cif.iucr_writer import write_iucr_cif

    project = _project(
        'mixed',
        tmp_path,
        _collection(_structure(name='phase1')),
        _collection(
            _single_crystal_experiment('sc'),
            _powder_experiment('cwl'),
        ),
    )

    text = write_iucr_cif(project).read_text(encoding='utf-8')

    block_names = [
        line.removeprefix('data_') for line in text.splitlines() if line.startswith('data_')
    ]
    assert len(block_names) == len(set(block_names))
    assert 'phase1' in block_names
    assert 'phase1_2' in block_names
    assert '_pd_block_id                           phase1_2' in text


def test_iucr_loop_rows_are_not_padded_to_tag_width():
    from easydiffraction.io.cif.iucr_writer import _write_loop

    lines = []

    _write_loop(
        lines,
        ('_atom_site_aniso.label', '_atom_site_aniso.U_11'),
        (('Tb', 0.00658189), ('O1', 0.0)),
    )

    assert lines == [
        'loop_',
        '_atom_site_aniso.label',
        '_atom_site_aniso.U_11',
        '  Tb 0.00658189',
        '  O1 0.',
    ]


def test_iucr_atom_site_rows_preserve_parameter_uncertainties():
    from easydiffraction.datablocks.structure.categories.atom_sites.default import AtomSite
    from easydiffraction.io.cif.iucr_writer import _atom_site_row
    from easydiffraction.io.cif.iucr_writer import _atom_site_tags
    from easydiffraction.io.cif.iucr_writer import _write_loop
    from easydiffraction.io.cif.serialize import format_param_value

    atom_site = AtomSite()
    atom_site.label = 'Si1'
    atom_site.type_symbol = 'Si'
    atom_site.fract_x = 11.98509310
    atom_site.fract_x.free = True
    atom_site.fract_x.uncertainty = 0.03069505
    lines = []

    _write_loop(lines, _atom_site_tags('B'), (_atom_site_row(atom_site),))

    assert format_param_value(atom_site.fract_x) in lines[-1].split()


def test_iucr_atom_site_aniso_rows_preserve_parameter_uncertainties():
    from easydiffraction.datablocks.structure.categories.atom_site_aniso.default import (
        AtomSiteAniso,
    )
    from easydiffraction.io.cif.iucr_writer import _atom_site_aniso_row
    from easydiffraction.io.cif.iucr_writer import _atom_site_aniso_tags
    from easydiffraction.io.cif.iucr_writer import _write_loop
    from easydiffraction.io.cif.serialize import format_param_value

    aniso_site = AtomSiteAniso()
    aniso_site.label = 'Si1'
    aniso_site.adp_11 = 0.00658189
    aniso_site.adp_11.free = True
    aniso_site.adp_11.uncertainty = 0.00014
    lines = []

    _write_loop(lines, _atom_site_aniso_tags('B'), (_atom_site_aniso_row(aniso_site),))

    assert format_param_value(aniso_site.adp_11) in lines[-1].split()


def test_iucr_extension_items_preserve_parameter_uncertainties():
    from easydiffraction.core.validation import AttributeSpec
    from easydiffraction.core.variable import Parameter
    from easydiffraction.io.cif.iucr_writer import _iucr_items
    from easydiffraction.io.cif.iucr_writer import _write_item
    from easydiffraction.io.cif.serialize import format_param_value

    scale = Parameter(
        name='scale',
        value_spec=AttributeSpec(default=1.0),
        cif_handler=CifHandler(
            names=['_sc_crystal_block.scale'],
            iucr_name='_easydiffraction_sc_crystal_block.scale',
        ),
    )
    scale.value = 2.87438284
    scale.free = True
    scale.uncertainty = 0.0274
    owner = SimpleNamespace(scale=scale)
    tag, value = _iucr_items(owner, ('scale',))[0]
    lines = []

    _write_item(lines, tag, value)

    assert format_param_value(scale) in lines[0]


def test_iucr_extinction_extensions_preserve_parameter_uncertainties():
    from easydiffraction.datablocks.experiment.categories.extinction.becker_coppens import (
        BeckerCoppensExtinction,
    )
    from easydiffraction.io.cif.iucr_writer import _extinction_items
    from easydiffraction.io.cif.iucr_writer import _write_item
    from easydiffraction.io.cif.serialize import format_param_value

    extinction = BeckerCoppensExtinction()
    extinction.radius = 24.83171997
    extinction.radius.free = True
    extinction.radius.uncertainty = 0.4931
    experiment = SimpleNamespace(extinction=extinction)
    items = {item.tag: item.value for item in _extinction_items(experiment, extension=True)}
    lines = []

    _write_item(
        lines,
        '_easydiffraction_extinction.radius',
        items['_easydiffraction_extinction.radius'],
    )

    assert format_param_value(extinction.radius) in lines[0]


def test_adp_family_returns_beta_for_beta_type():
    from easydiffraction.io.cif.iucr_writer import _adp_family

    atom = SimpleNamespace(adp_type=SimpleNamespace(value='beta'))
    assert _adp_family(atom) == 'beta'


def test_adp_iso_family_maps_beta_to_b_column():
    from easydiffraction.io.cif.iucr_writer import _adp_iso_family

    # beta has no isotropic CIF tag; its equivalent iso is written in the
    # B_iso_or_equiv column.
    atom = SimpleNamespace(adp_type=SimpleNamespace(value='beta'))
    assert _adp_iso_family(atom) == 'B'


def test_atom_site_aniso_tags_for_beta_family():
    from easydiffraction.io.cif.iucr_writer import _atom_site_aniso_tags

    tags = _atom_site_aniso_tags('beta')
    assert '_atom_site_aniso.beta_11' in tags
    assert '_atom_site_aniso.beta_22' in tags
    assert '_atom_site_aniso.beta_23' in tags
