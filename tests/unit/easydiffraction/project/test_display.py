# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Unit tests for project/display.py."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from easydiffraction.project.display import PatternOptionStatus
from easydiffraction.project.display import ProjectDisplay


def _make_project_stub() -> tuple[SimpleNamespace, list[tuple[str, tuple, dict]]]:
    calls: list[tuple[str, tuple, dict]] = []

    def record(name: str):
        def _recorder(*args, **kwargs):
            calls.append((name, args, kwargs))

        return _recorder

    analysis_display = SimpleNamespace(
        all_params=record('all_params'),
        fittable_params=record('fittable_params'),
        free_params=record('free_params'),
        how_to_access_parameters=record('how_to_access_parameters'),
        parameter_cif_uids=record('parameter_cif_uids'),
        fit_results=record('fit_results'),
    )
    plotter = SimpleNamespace(
        plot_param_correlations=record('plot_param_correlations'),
        plot_param_series=record('plot_param_series'),
        plot_posterior_pairs=record('plot_posterior_pairs'),
        plot_param_distribution=record('plot_param_distribution'),
        plot_posterior_predictive=record('plot_posterior_predictive'),
        plot_meas=record('plot_meas'),
        plot_calc=record('plot_calc'),
        plot_meas_vs_calc=record('plot_meas_vs_calc'),
    )
    project = SimpleNamespace(
        analysis=SimpleNamespace(display=analysis_display),
        rendering=SimpleNamespace(plotter=plotter),
    )
    return project, calls


def _make_statuses(
    *,
    measured: bool = False,
    calculated: bool = False,
    background: bool = False,
    residual: bool = False,
    bragg: bool = False,
    excluded: bool = False,
    uncertainty: bool = False,
    uncertainty_reason: str = 'Posterior predictive data is unavailable.',
) -> list[PatternOptionStatus]:
    return [
        PatternOptionStatus(
            name='auto',
            description='auto',
            available=True,
            auto_included=True,
            reason='',
        ),
        PatternOptionStatus(
            name='measured',
            description='measured',
            available=measured,
            auto_included=False,
            reason='' if measured else 'Measured unavailable',
        ),
        PatternOptionStatus(
            name='calculated',
            description='calculated',
            available=calculated,
            auto_included=False,
            reason='' if calculated else 'Calculated unavailable',
        ),
        PatternOptionStatus(
            name='background',
            description='background',
            available=background,
            auto_included=False,
            reason='' if background else 'Background unavailable',
        ),
        PatternOptionStatus(
            name='residual',
            description='residual',
            available=residual,
            auto_included=False,
            reason='' if residual else 'Residual unavailable',
        ),
        PatternOptionStatus(
            name='bragg',
            description='bragg',
            available=bragg,
            auto_included=False,
            reason='' if bragg else 'Bragg unavailable',
        ),
        PatternOptionStatus(
            name='excluded',
            description='excluded',
            available=excluded,
            auto_included=False,
            reason='' if excluded else 'Excluded unavailable',
        ),
        PatternOptionStatus(
            name='uncertainty',
            description='uncertainty',
            available=uncertainty,
            auto_included=False,
            reason='' if uncertainty else uncertainty_reason,
        ),
    ]


def test_parameter_display_delegates_to_analysis_display():
    project, calls = _make_project_stub()
    display = ProjectDisplay(project)

    display.parameters.all()
    display.parameters.fittable()
    display.parameters.free()
    display.parameters.access()
    display.parameters.cif_uids()

    assert [name for name, _args, _kwargs in calls] == [
        'all_params',
        'fittable_params',
        'free_params',
        'how_to_access_parameters',
        'parameter_cif_uids',
    ]


def test_fit_display_delegates_to_analysis_and_rendering():
    project, calls = _make_project_stub()
    display = ProjectDisplay(project)

    display.fit.results()
    display.fit.correlations(
        threshold=0.75,
        precision=3,
        max_parameters=4,
        show_diagonal=False,
    )
    display.fit.series(param='scale', versus='temperature')

    assert calls[0] == ('fit_results', (), {})
    assert calls[1] == (
        'plot_param_correlations',
        (),
        {
            'threshold': 0.75,
            'precision': 3,
            'max_parameters': 4,
            'show_diagonal': False,
        },
    )
    assert calls[2] == (
        'plot_param_series',
        (),
        {'param': 'scale', 'versus': 'temperature'},
    )


def test_posterior_display_delegates_to_rendering_plotter():
    project, calls = _make_project_stub()
    display = ProjectDisplay(project)

    display.posterior.pairs(parameters=['a'], threshold=0.5, max_parameters=3)
    display.posterior.distribution('a')
    display.posterior.predictive(
        'hrpt',
        style='draws',
        x_min=1.0,
        x_max=2.0,
        show_residual=True,
        x='d_spacing',
    )

    assert calls[0][0] == 'plot_posterior_pairs'
    assert calls[0][2]['parameters'] == ['a']
    assert calls[0][2]['threshold'] == 0.5
    assert calls[0][2]['max_parameters'] == 3
    assert calls[1] == ('plot_param_distribution', ('a',), {})
    assert calls[2] == (
        'plot_posterior_predictive',
        (),
        {
            'expt_name': 'hrpt',
            'style': 'draws',
            'x_min': 1.0,
            'x_max': 2.0,
            'show_residual': True,
            'x': 'd_spacing',
        },
    )


def test_pattern_auto_routes_measured_and_excluded_to_plot_meas():
    project, calls = _make_project_stub()
    display = ProjectDisplay(project)
    display._pattern_option_statuses = lambda expt_name: _make_statuses(
        measured=True,
        excluded=True,
    )

    display.pattern('hrpt')

    assert calls == [
        (
            'plot_meas',
            (),
            {
                'expt_name': 'hrpt',
                'x_min': None,
                'x_max': None,
                'x': None,
                'show_excluded': True,
            },
        )
    ]


def test_pattern_uncertainty_routes_to_posterior_predictive():
    project, calls = _make_project_stub()
    display = ProjectDisplay(project)
    display._pattern_option_statuses = lambda expt_name: _make_statuses(
        measured=True,
        calculated=True,
        residual=True,
        excluded=True,
        uncertainty=True,
    )

    display.pattern(
        'hrpt',
        x_min=1.0,
        x_max=2.0,
        include=('measured', 'calculated', 'uncertainty', 'residual', 'excluded'),
    )

    assert calls == [
        (
            'plot_posterior_predictive',
            (),
            {
                'expt_name': 'hrpt',
                'style': 'band',
                'x_min': 1.0,
                'x_max': 2.0,
                'show_residual': True,
                'show_excluded': True,
                'x': None,
            },
        )
    ]


def test_pattern_rejects_excluded_with_custom_x():
    project, _calls = _make_project_stub()
    display = ProjectDisplay(project)
    display._pattern_option_statuses = lambda expt_name: _make_statuses(
        measured=True,
        excluded=True,
    )

    with pytest.raises(ValueError, match='default x-axis'):
        display.pattern('hrpt', include=('measured', 'excluded'), x='d_spacing')


def test_show_pattern_options_renders_table(monkeypatch):
    project, _calls = _make_project_stub()
    display = ProjectDisplay(project)
    display._pattern_option_statuses = lambda expt_name: _make_statuses(
        measured=True,
        calculated=True,
    )
    captured: dict[str, object] = {}

    def fake_render_table(*, columns_headers, columns_alignment, columns_data):
        captured['columns_headers'] = columns_headers
        captured['columns_alignment'] = columns_alignment
        captured['columns_data'] = columns_data

    monkeypatch.setattr('easydiffraction.project.display.render_table', fake_render_table)

    display.show_pattern_options('hrpt')

    assert captured['columns_headers'] == ['Option', 'Description', 'Available', 'Auto', 'Reason']
    assert captured['columns_alignment'] == ['left', 'left', 'center', 'center', 'left']
    assert captured['columns_data'][0][0] == 'auto'
    assert captured['columns_data'][1][0] == 'measured'
