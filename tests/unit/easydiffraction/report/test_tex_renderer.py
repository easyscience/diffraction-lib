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
