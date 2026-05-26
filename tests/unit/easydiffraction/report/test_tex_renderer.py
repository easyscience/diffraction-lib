# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations


def _minimal_context() -> dict[str, object]:
    """Return the smallest report context accepted by TeX templates."""
    return {
        'project': {
            'name': 'report_project',
            'title': 'Report Project',
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


def test_render_tex_report_keeps_latex_graphicspath_braces():
    from easydiffraction.report.tex_renderer import render_tex_report

    for style in ('iucr', 'revtex'):
        tex = render_tex_report(_minimal_context(), style=style)

        assert r'\graphicspath{{figures/}}' in tex


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
        }
    ]

    for style in ('iucr', 'revtex'):
        tex = render_tex_report(context, style=style)

        assert '11.985(31)' in tex
        assert '0.00658(14)' in tex
        assert '-0.00048(25)' in tex
