# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for HTML report rendering."""

from __future__ import annotations

import numpy as np


def _field(label: str, units: str = '') -> dict[str, str]:
    return {'label': label, 'units': units}


def _category_row(
    name: str,
    value: object,
    *,
    label: str | None = None,
    html_label: str | None = None,
    html_units: str = '',
    numeric: bool = False,
    number: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        'name': name,
        'label': label or name,
        'html_label': html_label or label or name,
        'html_units': html_units,
        'value': value,
        'numeric': numeric,
        'number': number,
    }


def _category_column(
    name: str,
    *,
    label: str | None = None,
    html_label: str | None = None,
    html_units: str = '',
    numeric: bool = False,
) -> dict[str, object]:
    return {
        'name': name,
        'label': label or name,
        'html_label': html_label or label or name,
        'html_units': html_units,
        'numeric': numeric,
    }


def _category_cell(
    value: object,
    *,
    numeric: bool = False,
    number: dict[str, object] | None = None,
) -> dict[str, object]:
    return {'value': value, 'numeric': numeric, 'number': number}


def _number(
    left: str,
    right: str,
    *,
    has_decimal: bool = True,
    left_ch: int = 1,
    right_ch: int = 1,
) -> dict[str, object]:
    return {
        'left': left,
        'right': right,
        'has_decimal': has_decimal,
        'left_ch': left_ch,
        'right_ch': right_ch,
    }


def _context() -> dict[str, object]:
    return {
        'project': {
            'name': 'report_project',
            'title': 'Report Project',
            'description': 'Project description.',
            'n_phases': 1,
            'n_experiments': 0,
        },
        'publication': {
            'body': {'title': '', 'abstract': '', 'synopsis': '', 'keywords': ''},
            'authors': [],
            'journal': {'name_full': '', 'year': '', 'paper_doi': ''},
            'contact_author': {'name': '', 'email': ''},
        },
        'metadata': {
            'generated_at': '2026-05-26T00:00:00Z',
            'easydiffraction_version': '0.0',
        },
        'refinement': {
            'fit_result': {
                'reduced_chi_square': None,
                'r_factor_all': None,
                'wr_factor_all': None,
            },
            'parameters': {'free': 0, 'total': 0},
            'constraints': 0,
            'rows': [
                {
                    'label': 'Reduced chi-square',
                    'value': '1.23',
                    'numeric': True,
                    'number': _number('1', '23', right_ch=2),
                },
            ],
        },
        'software': {
            'framework': {'name': 'EasyDiffraction', 'version': '0.0'},
            'calculator': {'name': 'cryspy', 'version': '0.0'},
            'minimizer': {'name': 'lmfit', 'version': '0.0'},
        },
        'structures': [
            {
                'id': 'phase',
                'space_group': 'P 1',
                'crystal_system': 'triclinic',
                'cell': {
                    'length_a': '11.985(31)',
                    'length_b': '2.()',
                    'length_c': '3.()',
                    'angle_alpha': '90.()',
                    'angle_beta': '90.()',
                    'angle_gamma': '90.()',
                },
                'cell_display': {
                    'length_a': _field('a', 'A'),
                    'length_b': _field('b', 'A'),
                    'length_c': _field('c', 'A'),
                    'angle_alpha': _field('alpha', 'deg'),
                    'angle_beta': _field('beta', 'deg'),
                    'angle_gamma': _field('gamma', 'deg'),
                },
                'atom_sites': [
                    {
                        'label': 'Si1',
                        'type_symbol': 'Si',
                        'fract_x': '11.985(31)',
                        'fract_y': '0.',
                        'fract_z': '0.',
                        'occupancy': '1.',
                        'adp_iso': '0.00658(14)',
                    }
                ],
                'atom_site_display': {
                    'fract_x': _field('x'),
                    'fract_y': _field('y'),
                    'fract_z': _field('z'),
                    'adp_iso': _field('Uiso', 'A^2'),
                },
                'atom_site_aniso': [
                    {
                        'label': 'Si1',
                        'adp_11': '0.00658(14)',
                        'adp_22': '0.00488(29)',
                        'adp_33': '0.00488144',
                        'adp_12': '-0.00048(25)',
                        'adp_13': '0.',
                        'adp_23': '0.00189(13)',
                    }
                ],
                'atom_site_aniso_display': {
                    'adp_11': _field('U11', 'A^2'),
                    'adp_22': _field('U22', 'A^2'),
                    'adp_33': _field('U33', 'A^2'),
                    'adp_12': _field('U12', 'A^2'),
                    'adp_13': _field('U13', 'A^2'),
                    'adp_23': _field('U23', 'A^2'),
                },
                'categories': [
                    {
                        'kind': 'item',
                        'title': 'cell',
                        'rows': [
                            _category_row(
                                'length_a',
                                '11.985(31)',
                                html_label='a',
                                html_units='Å',
                                numeric=True,
                                number=_number(
                                    '11',
                                    '985(31)',
                                    left_ch=2,
                                    right_ch=7,
                                ),
                            ),
                        ],
                    },
                    {
                        'kind': 'loop',
                        'title': 'atom_site',
                        'scalar_rows': [],
                        'columns': [
                            _category_column('label'),
                            _category_column(
                                'adp_iso',
                                html_label=r'\(U_{\mathrm{iso}}\)',
                                html_units=r'\(\mathring{\mathrm{A}}^2\)',
                                numeric=True,
                            ),
                        ],
                        'rows': [
                            {
                                'cells': [
                                    _category_cell('Si1'),
                                    _category_cell(
                                        '0.00658(14)',
                                        numeric=True,
                                        number=_number(
                                            '0',
                                            '00658(14)',
                                            right_ch=9,
                                        ),
                                    ),
                                ],
                            },
                        ],
                    },
                    {
                        'kind': 'loop',
                        'title': 'atom_site_aniso',
                        'scalar_rows': [],
                        'columns': [
                            _category_column('label'),
                            _category_column(
                                'adp_12',
                                html_label=r'\(U_{12}\)',
                                numeric=True,
                            ),
                        ],
                        'rows': [
                            {
                                'cells': [
                                    _category_cell('Si1'),
                                    _category_cell(
                                        '-0.00048(25)',
                                        numeric=True,
                                        number=_number(
                                            '-0',
                                            '00048(25)',
                                            left_ch=2,
                                            right_ch=9,
                                        ),
                                    ),
                                ],
                            },
                        ],
                    },
                ],
            }
        ],
        'experiments': [],
        'figures': {'fit_per_experiment': {}},
    }


def test_render_html_report_preserves_structure_uncertainty_text():
    from easydiffraction.report.html_renderer import render_html_report

    html = render_html_report(_context())

    assert '11.985(31)' in html
    assert '0.00658(14)' in html
    assert '-0.00048(25)' in html
    assert '<h2>Publication</h2>' not in html
    assert '<h2>Project Description</h2>' in html
    assert '<h2>Project Summary</h2>' in html
    assert '<section class="numbered-section">' in html
    assert '<td class="key">Short name</td>' in html
    assert '<th>Short name</th>' not in html
    assert 'margin-right: 0.5em;' in html
    assert '--wide-colsep: 3pt;' in html
    assert 'class="numeric"' in html
    assert 'class="number"' in html
    assert '--number-left: 2ch; --number-right: 7ch' in html
    assert 'aria-label="1.23"' in html


def test_render_html_report_uses_plotly_fit_style_order():
    from easydiffraction.display.plotters.base import BraggTickSet
    from easydiffraction.report.html_renderer import render_html_report

    context = _context()
    context['project']['n_experiments'] = 1
    context['experiments'] = [
        {
            'id': 'hrpt',
            'type': {
                'sample_form': 'powder',
                'radiation_probe': 'neutron',
                'beam_mode': 'constant wavelength',
                'scattering_type': 'bragg',
            },
            'calculator': {'type': 'cryspy'},
            'diffrn': {'ambient_temperature': '', 'ambient_pressure': ''},
            'diffrn_display': {
                'ambient_temperature': _field('Temperature', 'K'),
                'ambient_pressure': _field('Pressure', 'kPa'),
            },
            'fit_data': {
                'x': {'values': [1.0, 2.0], 'display_name': '2theta'},
                'axes_labels': ['2θ (deg)', 'Intensity (arb. units)'],
                'series': {
                    'meas': {'values': [10.0, 11.0], 'su': [0.1, 0.2]},
                    'calc': {'values': [10.0, 12.0]},
                    'diff': {'values': [0.0, -1.0]},
                    'bkg': {'values': [5.0, 5.5]},
                },
                'bragg_tick_sets': (
                    BraggTickSet(
                        phase_id='phase-a',
                        x=np.array([1.5]),
                        h=np.array([1]),
                        k=np.array([0]),
                        ell=np.array([1]),
                        f_squared_calc=np.array([100.0]),
                        f_calc=np.array([10.0]),
                    ),
                ),
            },
        }
    ]

    html = render_html_report(context)

    measured = html.index('"name":"Measured (Imeas)"')
    background = html.index('"name":"Background (Ibkg)"')
    calculated = html.index('"name":"Total calculated (Icalc)"')
    residual = html.index('"name":"Residual (Imeas - Icalc)"')
    assert measured < background < calculated < residual
    assert '"legendrank":10' in html
    assert '"legendrank":20' in html
    assert '"legendrank":30' in html
    assert '"legendrank":40' in html
    assert '"error_y"' in html
    assert '"color":"rgb(31, 119, 180)"' in html
    assert '"name":"Bragg peaks: phase-a"' in html
    assert '"yaxis3"' in html
