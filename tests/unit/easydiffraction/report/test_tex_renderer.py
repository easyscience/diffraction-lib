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
        },
        'software': {
            'framework': {'name': 'EasyDiffraction', 'version': '0.0'},
            'calculator': {'name': 'cryspy', 'version': '0.0'},
            'minimizer': {'name': 'lmfit', 'version': '0.0'},
        },
        'structures': [],
        'experiments': [],
        'figures': {'fit_per_experiment': {}},
    }


def _latex_field(label: str, units: str = '') -> dict[str, str]:
    """Return one rendered-field metadata mapping."""
    return {'label': label, 'units': units}


def test_render_tex_report_renders_default_document():
    from easydiffraction.report.tex_renderer import render_tex_report

    context = _minimal_context()
    context['project']['description'] = 'Project description.'
    tex = render_tex_report(context)

    assert r'\documentclass[11pt,a4paper]{styles/iucrjournals}' in tex
    assert r'\title{Report Project}' in tex
    assert r'\author{}' in tex
    assert r'\begin{abstract}' in tex
    assert 'Project description.' in tex
    assert r'\section{Project Summary}' in tex
    assert r'\begin{table}[H]' in tex
    assert r'\toprule' in tex
    assert r'\bottomrule' in tex
    assert r'\section{Publication' not in tex


def test_render_tex_report_preserves_structure_uncertainty_text():
    from easydiffraction.report.tex_renderer import render_tex_report

    context = _minimal_context()
    context['structures'] = [
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
            'cell_latex': {
                'length_a': _latex_field('$a$', r'\AA'),
                'length_b': _latex_field('$b$', r'\AA'),
                'length_c': _latex_field('$c$', r'\AA'),
                'angle_alpha': _latex_field(r'$\alpha$', 'deg'),
                'angle_beta': _latex_field(r'$\beta$', 'deg'),
                'angle_gamma': _latex_field(r'$\gamma$', 'deg'),
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
            'atom_site_latex': {
                'adp_iso': _latex_field('$U_{iso}$', r'\AA^2'),
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
            'atom_site_aniso_latex': {
                'adp_11': _latex_field('$U_{11}$', r'\AA^2'),
                'adp_22': _latex_field('$U_{22}$', r'\AA^2'),
                'adp_33': _latex_field('$U_{33}$', r'\AA^2'),
                'adp_12': _latex_field('$U_{12}$', r'\AA^2'),
                'adp_13': _latex_field('$U_{13}$', r'\AA^2'),
                'adp_23': _latex_field('$U_{23}$', r'\AA^2'),
            },
        }
    ]

    tex = render_tex_report(context)

    assert '11.985(31)' in tex
    assert '0.00658(14)' in tex
    assert '-0.00048(25)' in tex
    assert (
        r'\subsubsection{Atom site parameters}' '\n\n'
        r'\begin{table}[H]' '\n'
        r'\begin{tabular}{llccccc}' '\n'
        r'\toprule' '\n'
        r'Label &'
    ) in tex
    assert r'\midrule' in tex


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
    assert r'xlabel={ time\_of\_flight (micro\_seconds) }' in tex
    assert r'ylabel={ intensity\_obs }' in tex
    assert r'\definecolor{ed_meas}{RGB}{31,119,180}' in tex
    assert 'line join=bevel' in tex


def test_render_tex_report_uses_composite_pgfplots_with_error_bars():
    from easydiffraction.display.plotters.base import BraggTickSet
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
                'ambient_temperature': _latex_field('Temperature', 'K'),
                'ambient_pressure': _latex_field('Pressure', 'kPa'),
            },
            'fit_data': {
                'x': {'values': [1.0, 2.0]},
                'axes_labels': ['2θ (degree)', 'Intensity (arb. units)'],
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

    tex = render_tex_report(context)

    assert r'\usepgfplotslibrary{groupplots}' in tex
    assert r'\begin{groupplot}' in tex
    assert 'group size=1 by 3' in tex
    assert 'mark layer=like plot' in tex
    assert 'y error=meas_su' in tex
    assert 'mark=|' in tex
    assert 'ytick={1}' in tex
    assert 'yticklabels={{phase-a}}' in tex
    assert 'ylabel={Residual}' in tex
    assert tex.index('color=ed_meas') < tex.index('color=ed_calc')


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
    assert not (tex_dir / 'styles' / 'stale.txt').exists()
    assert (tex_dir / 'styles' / 'iucrjournals.cls').is_file()
