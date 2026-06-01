# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations


def test_report_style_context_exposes_hex_and_rgb_values():
    from easydiffraction.report.style import report_style_context

    context = report_style_context()

    assert context['axis_hex'] == '#bec7d0'
    assert context['axis_rgb'] == '190,199,208'
    assert context['grid_hex'] == '#e0e0e0'
    assert context['grid_rgb'] == '226,226,226'
    assert context['chart_grid_rgb'] == '235,240,248'
    assert context['subtitle'] == 'EasyDiffraction Report'
    assert 'PT Sans' in context['html_font_family']
