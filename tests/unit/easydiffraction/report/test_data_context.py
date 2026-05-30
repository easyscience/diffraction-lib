# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for report data-context construction."""

from __future__ import annotations

from types import SimpleNamespace

import numpy as np


class _Descriptor:
    def __init__(self, value):
        self.value = value


class _XDescriptor:
    name = 'intensity_calc'
    units = 'none'

    @staticmethod
    def resolve_display_name(context):
        del context
        return 'I²calc'

    @staticmethod
    def resolve_display_units(context):
        del context
        return ''


class _TwoThetaDescriptor:
    name = 'two_theta'
    units = 'degrees'

    @staticmethod
    def resolve_display_name(context):
        del context
        return '2θ'

    @staticmethod
    def resolve_display_units(context):
        del context
        return 'deg'


def _parameter(name, value, uncertainty):
    from easydiffraction.core.validation import AttributeSpec
    from easydiffraction.core.variable import Parameter
    from easydiffraction.io.cif.handler import CifHandler

    parameter = Parameter(
        name=name,
        value_spec=AttributeSpec(default=0.0),
        cif_handler=CifHandler(names=[f'_{name}']),
    )
    parameter.value = value
    parameter.free = True
    parameter.uncertainty = uncertainty
    return parameter


def _structure() -> SimpleNamespace:
    return SimpleNamespace(
        name='phase',
        space_group=SimpleNamespace(
            name_h_m=_Descriptor('P 1'),
            crystal_system=_Descriptor('triclinic'),
        ),
        cell=SimpleNamespace(
            length_a=_parameter('length_a', 11.98509310, 0.03069505),
            length_b=_parameter('length_b', 2.0, None),
            length_c=_parameter('length_c', 3.0, None),
            angle_alpha=_parameter('angle_alpha', 90.0, None),
            angle_beta=_parameter('angle_beta', 90.0, None),
            angle_gamma=_parameter('angle_gamma', 90.0, None),
        ),
        atom_sites=[
            SimpleNamespace(
                label=_Descriptor('Si1'),
                type_symbol=_Descriptor('Si'),
                fract_x=_parameter('fract_x', 11.98509310, 0.03069505),
                fract_y=_parameter('fract_y', 0.0, None),
                fract_z=_parameter('fract_z', 0.0, None),
                occupancy=_parameter('occupancy', 1.0, None),
                adp_type=_Descriptor('Uani'),
                adp_iso=_parameter('adp_iso', 0.00658189, 0.00014),
            )
        ],
        atom_site_aniso=[
            SimpleNamespace(
                label=_Descriptor('Si1'),
                adp_11=_parameter('adp_11', 0.00658189, 0.00014),
                adp_22=_parameter('adp_22', 0.00488144, 0.00029),
                adp_33=_parameter('adp_33', 0.00488144, None),
                adp_12=_parameter('adp_12', -0.00048176, 0.00025),
                adp_13=_parameter('adp_13', 0.0, None),
                adp_23=_parameter('adp_23', 0.00188994, 0.00013),
            )
        ],
    )


def _experiment() -> SimpleNamespace:
    return SimpleNamespace(
        name='heidi',
        type=SimpleNamespace(
            sample_form=_Descriptor('single crystal'),
            beam_mode=_Descriptor('constant wavelength'),
            radiation_probe=_Descriptor('neutron'),
            scattering_type=_Descriptor('bragg'),
        ),
        calculator=SimpleNamespace(type=_Descriptor('cryspy')),
        diffrn=SimpleNamespace(),
        measured_range=None,
        x_descriptor=_XDescriptor(),
        fit_data_arrays=lambda: {
            'x': np.array([10.0, 20.0]),
            'meas': np.array([11.0, 19.0]),
            'meas_su': np.array([0.5, 0.7]),
            'calc': np.array([10.0, 20.0]),
            'diff': np.array([1.0, -1.0]),
            'bkg': None,
        },
        refln=SimpleNamespace(
            intensity_meas=np.array([11.0, 19.0]),
            intensity_calc=np.array([10.0, 20.0]),
            intensity_meas_su=np.array([0.5, 0.7]),
        ),
    )


def _project() -> SimpleNamespace:
    return SimpleNamespace(
        name='demo',
        info=SimpleNamespace(title=_Descriptor('Demo'), description=_Descriptor(None)),
        structures={'phase': _structure()},
        experiments={'heidi': _experiment()},
        analysis=SimpleNamespace(
            fit_result=SimpleNamespace(),
            software=SimpleNamespace(),
            constraints=[],
        ),
        publication=SimpleNamespace(),
    )


def test_report_data_context_builds_fit_data():
    from easydiffraction.report.data_context import build_report_data_context

    context = build_report_data_context(_project())

    fit_data = context['experiments'][0]['fit_data']
    assert fit_data['axes_labels'] == ['I²calc', 'I²meas']
    assert list(fit_data['series']['meas']['su']) == [0.5, 0.7]
    assert list(fit_data['series']['calc']['values']) == [10.0, 20.0]
    assert list(fit_data['series']['diff']['values']) == [1.0, -1.0]
    assert fit_data['bragg_tick_sets'] == ()


def test_report_data_context_builds_powder_bragg_tick_sets():
    from easydiffraction.report.data_context import build_report_data_context

    experiment = _experiment()
    experiment.type.sample_form = _Descriptor('powder')
    experiment.x_descriptor = _TwoThetaDescriptor()
    experiment.fit_data_arrays = lambda: {
        'x': np.array([1.0, 2.0]),
        'meas': np.array([11.0, 19.0]),
        'meas_su': np.array([0.5, 0.7]),
        'calc': np.array([10.0, 20.0]),
        'diff': np.array([1.0, -1.0]),
        'bkg': np.array([2.0, 2.5]),
    }
    experiment.refln = SimpleNamespace(
        phase_id=np.array(['phase-a']),
        two_theta=np.array([1.5]),
        index_h=np.array([1]),
        index_k=np.array([0]),
        index_l=np.array([1]),
        f_squared_calc=np.array([100.0]),
        f_calc=np.array([10.0]),
    )
    project = _project()
    project.experiments = {'hrpt': experiment}

    context = build_report_data_context(project)

    tick_sets = context['experiments'][0]['fit_data']['bragg_tick_sets']
    assert [tick_set.phase_id for tick_set in tick_sets] == ['phase-a']
    assert list(tick_sets[0].x) == [1.5]


def test_report_data_context_preserves_structure_uncertainties():
    from easydiffraction.report.data_context import build_report_data_context

    context = build_report_data_context(_project())
    structure = context['structures'][0]

    assert structure['cell']['length_a'] == '11.985(31)'
    assert structure['atom_sites'][0]['fract_x'] == '11.985(31)'
    assert structure['atom_sites'][0]['adp_iso'] == '0.00658(14)'
    assert structure['atom_site_aniso'][0]['adp_12'] == '-0.00048(25)'


def test_report_category_context_keeps_numeric_string_ids_as_text():
    from easydiffraction.datablocks.experiment.categories.background.line_segment import (
        LineSegmentBackground,
    )
    from easydiffraction.report.data_context import _collection_category_context

    category = LineSegmentBackground()
    category.create(id='10', x=10.0, y=2.0)
    category.create(id='30', x=30.0, y=3.0)

    context = _collection_category_context(category)

    assert context['colspec'] == 'cS[table-format=2.0]S[table-format=1.0]'
    assert [(column['latex_label'], column['numeric']) for column in context['columns']] == [
        ('ID', False),
        ('$x$', True),
        ('Intensity', True),
    ]
    assert context['rows'][0]['cells'][1]['number'] == {
        'left': '10',
        'right': '',
        'has_decimal': False,
        'left_ch': 2,
        'right_ch': 1,
    }
    assert context['rows'][0]['cells'][2]['number'] == {
        'left': '2',
        'right': '',
        'has_decimal': True,
        'left_ch': 1,
        'right_ch': 1,
    }


def test_report_key_value_colspec_uses_numeric_table_format():
    from easydiffraction.report.data_context import _key_value_colspec

    rows = [
        {'value': '11.985(31)', 'numeric': True},
        {'value': '2.', 'numeric': True},
        {'value': 'not refined', 'numeric': False},
    ]

    assert _key_value_colspec(rows) == 'lS[table-format=2.3(2)]'


def test_report_loop_rows_skip_identifier_only_rows():
    from easydiffraction.report.data_context import _loop_row_has_report_values

    empty_row = {
        'cells': [
            {'value': '1'},
            {'value': ''},
            {'value': None},
        ],
    }
    populated_row = {
        'cells': [
            {'value': '1'},
            {'value': '10.5'},
            {'value': None},
        ],
    }

    assert not _loop_row_has_report_values(empty_row)
    assert _loop_row_has_report_values(populated_row)


def test_report_data_loop_rows_are_display_truncated():
    from easydiffraction.report.data_context import _REPORT_LOOP_DISPLAY_LIMIT
    from easydiffraction.report.data_context import _truncate_loop_rows

    rows = [
        {
            'cells': [
                {'value': str(index), 'numeric': False, 'number': None},
                {'value': float(index), 'numeric': False, 'number': None},
            ],
        }
        for index in range(_REPORT_LOOP_DISPLAY_LIMIT + 5)
    ]

    truncated = _truncate_loop_rows(rows)

    assert len(truncated) == _REPORT_LOOP_DISPLAY_LIMIT + 1
    assert truncated[0]['cells'][0]['value'] == '0'
    assert truncated[9]['cells'][0]['value'] == '9'
    assert truncated[10]['cells'][0]['value'] == '...'
    assert truncated[10]['cells'][1]['value'] == ''
    assert truncated[11]['cells'][0]['value'] == '15'
    assert truncated[-1]['cells'][0]['value'] == '24'


def test_report_pd_data_columns_use_compact_labels():
    from easydiffraction.datablocks.experiment.categories.data.bragg_pd import (
        PdCwlData,
    )
    from easydiffraction.report.data_context import _collection_category_context

    category = PdCwlData()
    category._create_items_set_xcoord_and_id(np.array([10.0]))

    context = _collection_category_context(category)

    assert [(column['latex_label'], column['html_label']) for column in context['columns']] == [
        (r'$2\theta$', r'\(2\theta\)'),
        ('ID', 'ID'),
        (r'$d$', r'\(d\)'),
        (r'$I_{\mathrm{meas}}$', r'\(I_{\mathrm{meas}}\)'),
        (
            r'$\sigma(I_{\mathrm{meas}})$',
            r'\(\sigma(I_{\mathrm{meas}})\)',
        ),
        (r'$I_{\mathrm{calc}}$', r'\(I_{\mathrm{calc}}\)'),
        (r'$I_{\mathrm{bkg}}$', r'\(I_{\mathrm{bkg}}\)'),
        ('Status', 'Status'),
    ]


def test_report_powder_refln_columns_use_compact_labels():
    from easydiffraction.analysis.calculators.base import PowderReflnRecord
    from easydiffraction.datablocks.experiment.categories.refln.bragg_pd import (
        PowderCwlReflnData,
    )
    from easydiffraction.report.data_context import _collection_category_context

    category = PowderCwlReflnData()
    category._replace_from_records([
        PowderReflnRecord(
            phase_id='phase',
            d_spacing=1.0,
            sin_theta_over_lambda=0.5,
            index_h=1,
            index_k=0,
            index_l=1,
            f_calc=2.0,
            f_squared_calc=4.0,
            two_theta=20.0,
        )
    ])

    context = _collection_category_context(category)

    assert [(column['latex_label'], column['html_label']) for column in context['columns']] == [
        ('ID', 'ID'),
        ('Phase', 'Phase'),
        (r'$d$', r'\(d\)'),
        (r'$\sin\theta/\lambda$', r'\(\sin\theta/\lambda\)'),
        (r'$h$', r'\(h\)'),
        (r'$k$', r'\(k\)'),
        (r'$l$', r'\(l\)'),
        (r'$F_{\mathrm{calc}}$', r'\(F_{\mathrm{calc}}\)'),
        (r'$F^2_{\mathrm{calc}}$', r'\(F^2_{\mathrm{calc}}\)'),
        (r'$2\theta$', r'\(2\theta\)'),
    ]


def test_report_atom_site_adp_column_uses_active_b_u_labels():
    from easydiffraction.datablocks.structure.item.base import Structure
    from easydiffraction.report.data_context import _collection_category_context

    structure = Structure(name='phase')
    structure.atom_sites.create(
        label='Si1',
        type_symbol='Si',
        adp_type='Biso',
        adp_iso=0.5,
    )
    structure.atom_sites.create(
        label='O1',
        type_symbol='O',
        adp_type='Uiso',
        adp_iso=0.006,
    )

    context = _collection_category_context(structure.atom_sites)
    adp_column = next(column for column in context['columns'] if column['name'] == 'adp_iso')

    assert adp_column['label'] == 'Biso / Uiso'
    assert adp_column['html_label'] == r'\(B_{\mathrm{iso}}\) / \(U_{\mathrm{iso}}\)'
    assert adp_column['latex_label'] == r'$B_{\mathrm{iso}}$ / $U_{\mathrm{iso}}$'


def test_report_atom_site_aniso_adp_column_uses_active_b_label():
    from easydiffraction.datablocks.structure.item.base import Structure
    from easydiffraction.report.data_context import _collection_category_context

    structure = Structure(name='phase')
    structure.atom_sites.create(
        label='Si1',
        type_symbol='Si',
        adp_iso=0.5,
    )
    structure.atom_sites['Si1'].adp_type = 'Bani'
    structure._sync_atom_site_aniso()

    context = _collection_category_context(structure.atom_site_aniso)
    adp_column = next(column for column in context['columns'] if column['name'] == 'adp_11')

    assert adp_column['label'] == 'B11'
    assert adp_column['html_label'] == r'\(B_{11}\)'
    assert adp_column['latex_label'] == r'$B_{11}$'


def test_report_number_parts_split_decimal_and_uncertainty_text():
    from easydiffraction.report.data_context import _number_parts

    assert _number_parts('0.584(20)') == {
        'left': '0',
        'right': '584(20)',
        'has_decimal': True,
    }
    assert _number_parts('.5') == {
        'left': '0',
        'right': '5',
        'has_decimal': True,
    }
    assert _number_parts('1.') == {
        'left': '1',
        'right': '',
        'has_decimal': True,
    }
    assert _number_parts('1') == {
        'left': '1',
        'right': '',
        'has_decimal': False,
    }


def test_report_descriptor_rows_normalize_angstrom_for_mathjax():
    from easydiffraction.core.display_handler import DisplayHandler
    from easydiffraction.core.validation import AttributeSpec
    from easydiffraction.core.variable import Parameter
    from easydiffraction.io.cif.handler import CifHandler
    from easydiffraction.report.data_context import _descriptor_rows

    parameter = Parameter(
        name='adp_iso',
        value_spec=AttributeSpec(default=0.0),
        display_handler=DisplayHandler(
            latex_name=r'$U_{\mathrm{iso}}$',
            latex_units=r'\AA$^2$',
        ),
        cif_handler=CifHandler(names=['_atom_site.U_iso_or_equiv']),
    )

    rows = _descriptor_rows([parameter])

    assert rows[0]['html_label'] == r'\(U_{\mathrm{iso}}\)'
    assert rows[0]['html_units'] == r'\(\mathring{\mathrm{A}}^2\)'


def test_report_descriptor_rows_preserve_mixed_mathjax_label_text():
    from easydiffraction.core.display_handler import DisplayHandler
    from easydiffraction.core.validation import AttributeSpec
    from easydiffraction.core.variable import Parameter
    from easydiffraction.io.cif.handler import CifHandler
    from easydiffraction.report.data_context import _descriptor_rows

    parameter = Parameter(
        name='twotheta_offset',
        value_spec=AttributeSpec(default=0.0),
        display_handler=DisplayHandler(
            latex_name=r'$2\theta$ offset',
            latex_units=r'$^\circ$',
        ),
        cif_handler=CifHandler(names=['_instr.2theta_offset']),
    )

    rows = _descriptor_rows([parameter])

    assert rows[0]['html_label'] == r'\(2\theta\) offset'
    assert rows[0]['html_units'] == r'\(\mathrm{deg}\)'
