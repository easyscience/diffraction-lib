# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import numpy as np


def _minimal_context() -> dict[str, object]:
    """Return the smallest report context accepted by TeX templates."""
    return {
        'project': {
            'name': 'report_project',
            'title': 'Report Project',
            'description': '',
            'n_phases': 0,
            'n_experiments': 0,
        },
        'publication': {
            'body': {
                'title': '',
                'abstract': '',
                'synopsis': '',
                'keywords': '',
            },
            'authors': [],
            'journal': {
                'name_full': '',
                'year': '',
                'paper_doi': '',
            },
            'contact_author': {
                'name': '',
                'email': '',
            },
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
            'parameters': {
                'free': 0,
                'total': 0,
            },
            'constraints': 0,
            'rows': [
                {'label': 'Free parameters', 'value': 0, 'numeric': True},
                {'label': 'Total parameters', 'value': 0, 'numeric': True},
                {'label': 'Constraints', 'value': 0, 'numeric': True},
            ],
            'colspec': 'lS[table-format=1.0]',
        },
        'software': {
            'framework': {'name': 'EasyDiffraction', 'version': '0.0'},
            'calculator': {'name': 'cryspy', 'version': '0.0'},
            'minimizer': {'name': 'lmfit', 'version': '0.0'},
        },
        'analysis': {
            'software': {
                'framework': {'name': 'EasyDiffraction', 'version': '0.0'},
                'calculator': {'name': 'cryspy', 'version': '0.0'},
                'minimizer': {'name': 'lmfit', 'version': '0.0'},
            },
            'categories': [],
        },
        'structures': [],
        'experiments': [],
        'figures': {'fit_per_experiment': {}},
    }


def _latex_field(label: str, units: str = '') -> dict[str, str]:
    """Return one rendered-field metadata mapping."""
    return {'label': label, 'units': units}


def _category_row(
    name: str,
    value: object,
    *,
    label: str | None = None,
    latex_label: str | None = None,
    html_label: str | None = None,
    units: str = '',
    latex_units: str = '',
    html_units: str = '',
    numeric: bool = False,
) -> dict[str, object]:
    """Return one generic category key-value row."""
    return {
        'name': name,
        'label': label or name,
        'latex_label': latex_label or label or name,
        'html_label': html_label or label or name,
        'units': units,
        'latex_units': latex_units or units,
        'html_units': html_units or units,
        'value': value,
        'numeric': numeric,
    }


def _category_column(
    name: str,
    *,
    label: str | None = None,
    latex_label: str | None = None,
    html_label: str | None = None,
    units: str = '',
    latex_units: str = '',
    html_units: str = '',
    numeric: bool = False,
) -> dict[str, object]:
    """Return one generic loop-category column."""
    return {
        'name': name,
        'label': label or name,
        'latex_label': latex_label or label or name,
        'html_label': html_label or label or name,
        'units': units,
        'latex_units': latex_units or units,
        'html_units': html_units or units,
        'numeric': numeric,
    }


def _category_cell(value: object, *, numeric: bool = False) -> dict[str, object]:
    """Return one generic loop-category cell."""
    return {'value': value, 'numeric': numeric}


def test_render_tex_report_renders_default_document():
    from easydiffraction.report.tex_renderer import render_tex_report

    context = _minimal_context()
    context['project']['description'] = 'Project description.'
    tex = render_tex_report(context)

    assert r'\documentclass[11pt]{article}' in tex
    assert r'\usepackage[margin=2.5cm]{geometry}' in tex
    assert r'\usepackage{fourier}' in tex
    assert r'\usepackage{longtable}' in tex
    assert r'\usepackage{paratype}' in tex
    assert r'\usepackage{titlesec}' in tex
    assert r'\sisetup{group-digits=false}' in tex
    assert r'\definecolor{rowshade}{RGB}{235,240,248}' in tex
    assert r'\definecolor{tableborder}{RGB}{190,199,208}' in tex
    assert r'\arrayrulecolor{tableborder}' in tex
    assert r'\setlength{\ReportTableColSep}{0.5em}' in tex
    assert r'\setlength{\tabcolsep}{\ReportTableColSep}' in tex
    assert r'\setlength{\LTleft}{0pt}' in tex
    assert (
        r'\newcommand{\rowColorsWithHeader}'
        r'{\rowcolors{1}{rowshade}{white}}'
    ) in tex
    assert (
        r'\newcommand{\rowColorsWithoutHeader}'
        r'{\rowcolors{1}{white}{rowshade}}'
    ) in tex
    assert r'\titlelabel{\thetitle.\enspace}' in tex
    assert r'\titleformat*{\section}' in tex
    assert r'{\Large EasyDiffraction Report\newline}' in tex
    assert r'{\LARGE Report Project\par}' in tex
    assert r'\section*{Project Description}' in tex
    assert 'Project description.' in tex
    assert r'\section{Project Summary}' in tex
    assert r'\begin{table}[H]' in tex
    assert r'\rowColorsWithoutHeader' in tex
    assert r'\rowColorsWithHeader' in tex
    assert r'\hline' in tex
    assert r'\section{Publication' not in tex


def test_render_tex_report_preserves_structure_uncertainty_text():
    from easydiffraction.report.tex_renderer import render_tex_report

    context = _minimal_context()
    context['structures'] = [
        {
            'id': 'phase',
            'categories': [
                {
                    'kind': 'item',
                    'title': 'cell',
                    'rows': [
                        _category_row(
                            'length_a',
                            '11.985(31)',
                            latex_label='$a$',
                            latex_units=r'\AA',
                            numeric=True,
                        ),
                        _category_row(
                            'angle_alpha',
                            '90',
                            latex_label=r'$\alpha$',
                            latex_units=r'$^\circ$',
                            numeric=True,
                        ),
                        _category_row('length_b', '2.', numeric=True),
                    ],
                    'has_numeric_values': True,
                    'value_column_numeric': True,
                    'colspec': 'lS[table-format=2.3(2)]',
                },
                {
                    'kind': 'loop',
                    'title': 'atom_site',
                    'scalar_rows': [],
                    'scalar_has_numeric_values': False,
                    'columns': [
                        _category_column('label'),
                        _category_column('fract_x', numeric=True),
                        _category_column(
                            'adp_iso',
                            latex_label='$U_{iso}$',
                            latex_units=r'\AA$^2$',
                            numeric=True,
                        ),
                    ],
                    'rows': [
                        {
                            'cells': [
                                _category_cell('Si1'),
                                _category_cell('11.985(31)', numeric=True),
                                _category_cell('0.00658(14)', numeric=True),
                            ],
                        },
                    ],
                    'colspec': ('lS[table-format=2.3(2)]S[table-format=1.5(2)]'),
                    'table_width': 'full',
                },
                {
                    'kind': 'loop',
                    'title': 'atom_site_aniso',
                    'scalar_rows': [],
                    'scalar_has_numeric_values': False,
                    'columns': [
                        _category_column('label'),
                        _category_column(
                            'adp_12',
                            latex_label='$U_{12}$',
                            numeric=True,
                        ),
                    ],
                    'rows': [
                        {
                            'cells': [
                                _category_cell('Si1'),
                                _category_cell('-0.00048(25)', numeric=True),
                            ],
                        },
                    ],
                    'colspec': 'lS[table-format=+1.5(2)]',
                    'table_width': 'half',
                },
            ],
        }
    ]

    tex = render_tex_report(context)

    assert '11.985(31)' in tex
    assert '0.00658(14)' in tex
    assert '-0.00048(25)' in tex
    assert r'$\alpha$ ($\mathrm{deg}$)' in tex
    assert r'$U_{iso}$ ($\mathring{\mathrm{A}}^2$)' in tex
    assert r'\subsubsection*{atom\_site}' in tex
    assert r'\multicolumn{1}{c|}{$U_{12}$}' in tex
    assert (
        r'\begin{longtable}{|lS[table-format=2.3(2)]'
        r'S[table-format=1.5(2)]|}'
    ) in tex
    assert r'\resizebox' not in tex
    assert r'\hline' in tex


def test_render_tex_report_escapes_plain_latex_field_labels():
    from easydiffraction.report.tex_renderer import render_tex_report

    context = _minimal_context()
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
            'diffrn': {
                'ambient_temperature': '',
                'ambient_pressure': '',
            },
            'diffrn_latex': {
                'ambient_temperature': _latex_field('ambient_temperature', 'K'),
                'ambient_pressure': _latex_field('ambient_pressure', 'kPa'),
            },
            'categories': [
                {
                    'kind': 'item',
                    'title': 'diffrn',
                    'rows': [
                        _category_row(
                            'ambient_temperature',
                            '',
                            label='ambient_temperature',
                            latex_label='ambient_temperature',
                            units='K',
                            latex_units='K',
                        ),
                        _category_row(
                            'ambient_pressure',
                            '',
                            label='ambient_pressure',
                            latex_label='ambient_pressure',
                            units='kPa',
                            latex_units='kPa',
                        ),
                    ],
                    'has_numeric_values': False,
                    'value_column_numeric': False,
                },
            ],
            'fit_data': {
                'x': {
                    'values': [1.0],
                    'latex_name': 'time_of_flight',
                    'latex_units': 'micro_seconds',
                },
                'axes_labels': ['time_of_flight (micro_seconds)', 'intensity_obs'],
                'series': {
                    'meas': {'values': [1.0], 'su': None, 'label': 'Measured'},
                    'calc': {'values': [1.0], 'label': 'Calculated'},
                    'diff': {'values': [0.0], 'label': 'Difference'},
                    'bkg': None,
                },
            },
        }
    ]

    tex = render_tex_report(context)

    assert r'ambient\_temperature (K)' in tex
    assert r'ambient\_pressure (kPa)' in tex


def test_save_tex_report_uses_composite_pgfplots_with_error_bars(tmp_path):
    from easydiffraction.display.plotters.base import BraggTickSet
    from easydiffraction.report.tex_renderer import save_tex_report

    context = _minimal_context()
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
            'diffrn': {
                'ambient_temperature': '',
                'ambient_pressure': '',
            },
            'diffrn_latex': {
                'ambient_temperature': _latex_field('Temperature', 'K'),
                'ambient_pressure': _latex_field('Pressure', 'kPa'),
            },
            'categories': [],
            'fit_data': {
                'x': {'values': [1.0, 2.0]},
                'axes_labels': ['2θ (deg)', 'Intensity (arb. units)'],
                'series': {
                    'meas': {'values': [10.0, 12.0], 'su': [0.2, 0.3]},
                    'calc': {'values': [9.0, 11.0]},
                    'diff': {'values': [1.0, 1.0]},
                    'bkg': {'values': [2.0, 2.5]},
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

    tex_path = tmp_path / 'reports' / 'tex' / 'report.tex'
    save_tex_report(object(), context, path=tex_path)
    figure_tex = (tex_path.parent / 'data' / 'hrpt.tex').read_text(
        encoding='utf-8',
    )
    csv_header = (
        (tex_path.parent / 'data' / 'hrpt.csv')
        .read_text(
            encoding='utf-8',
        )
        .splitlines()[0]
    )
    bragg_csv_header = (
        (tex_path.parent / 'data' / 'hrpt_phase-a.csv').read_text(encoding='utf-8').splitlines()[0]
    )

    assert r'\usepackage{fourier}' in figure_tex
    assert r'\usepackage{paratype}' in figure_tex
    assert r'\usepgfplotslibrary{groupplots}' in figure_tex
    assert r'\begin{groupplot}' in figure_tex
    assert 'group size=1 by 3' in figure_tex
    assert 'mark layer=like plot' in figure_tex
    assert 'mark options={fill=ed_meas, draw=ed_meas, fill opacity=1' in figure_tex
    assert 'table[x={_pd_proc.2theta_scan}, y={_pd_meas.intensity_total}' in figure_tex
    assert 'table[x={_pd_proc.2theta_scan}, y={_pd_calc.intensity_total}' in figure_tex
    assert r'\thisrow{_pd_meas.intensity_total}' in figure_tex
    assert 'hrpt_phase-a.csv' in figure_tex
    assert 'coordinates {' not in figure_tex
    assert 'mark=|' in figure_tex
    assert 'ytick={1}' in figure_tex
    assert 'yticklabels={{phase-a}}' in figure_tex
    assert figure_tex.index('color=ed_meas') < figure_tex.index('color=ed_calc')
    assert csv_header == (
        '_pd_proc.2theta_scan,_pd_data.point_id,_pd_proc.d_spacing,'
        '_pd_meas.intensity_total,_pd_meas.intensity_total_su,'
        '_pd_calc.intensity_total,_pd_calc.intensity_bkg,'
        '_pd_data.refinement_status'
    )
    assert bragg_csv_header == (
        '_refln.id,_refln.phase_id,_refln.index_h,_refln.index_k,'
        '_refln.index_l,_refln.f_calc,_refln.f_squared_calc,_refln.two_theta'
    )


def test_save_tex_report_removes_stale_managed_bundle_dirs(tmp_path):
    from easydiffraction.report.tex_renderer import save_tex_report

    tex_dir = tmp_path / 'reports' / 'tex'
    tex_path = tex_dir / 'report.tex'
    for dirname in ('data', 'styles', 'figures'):
        stale_path = tex_dir / dirname / 'stale.txt'
        stale_path.parent.mkdir(parents=True, exist_ok=True)
        stale_path.write_text('stale', encoding='utf-8')

    assert save_tex_report(object(), _minimal_context(), path=tex_path) == tex_path

    assert not (tex_dir / 'data').exists()
    assert not (tex_dir / 'figures').exists()
    assert not (tex_dir / 'styles').exists()
