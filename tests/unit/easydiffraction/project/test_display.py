# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Unit tests for project/display.py."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum
from easydiffraction.display.plotting import _MeasVsCalcPlotOptions
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
        _plot_posterior_predictive_request=record('_plot_posterior_predictive_request'),
        plot_meas=record('plot_meas'),
        plot_calc=record('plot_calc'),
        plot_meas_vs_calc=record('plot_meas_vs_calc'),
        _plot_meas_vs_calc_request=record('_plot_meas_vs_calc_request'),
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
            '_plot_posterior_predictive_request',
            (),
            {
                'expt_name': 'hrpt',
                'style': 'band',
                'plot_options': _MeasVsCalcPlotOptions(
                    x_min=1.0,
                    x_max=2.0,
                    show_residual=True,
                    show_background=False,
                    show_bragg=False,
                    show_excluded=True,
                    x=None,
                ),
            },
        )
    ]


def test_pattern_measured_and_calculated_suppresses_background_and_bragg():
    project, calls = _make_project_stub()
    display = ProjectDisplay(project)
    display._pattern_option_statuses = lambda expt_name: _make_statuses(
        measured=True,
        calculated=True,
        background=True,
        bragg=True,
    )

    display.pattern('hrpt', include=('measured', 'calculated'))

    assert calls == [
        (
            '_plot_meas_vs_calc_request',
            (),
            {
                'expt_name': 'hrpt',
                'plot_options': _MeasVsCalcPlotOptions(
                    x_min=None,
                    x_max=None,
                    show_residual=False,
                    show_background=False,
                    show_bragg=False,
                    show_excluded=False,
                    x=None,
                ),
            },
        )
    ]


def test_pattern_measured_and_calculated_can_enable_background_and_bragg():
    project, calls = _make_project_stub()
    display = ProjectDisplay(project)
    display._pattern_option_statuses = lambda expt_name: _make_statuses(
        measured=True,
        calculated=True,
        background=True,
        residual=True,
        bragg=True,
        excluded=True,
    )

    display.pattern(
        'hrpt',
        include=('measured', 'calculated', 'background', 'residual', 'bragg', 'excluded'),
    )

    assert calls == [
        (
            '_plot_meas_vs_calc_request',
            (),
            {
                'expt_name': 'hrpt',
                'plot_options': _MeasVsCalcPlotOptions(
                    x_min=None,
                    x_max=None,
                    show_residual=True,
                    show_background=True,
                    show_bragg=True,
                    show_excluded=True,
                    x=None,
                ),
            },
        )
    ]


def test_pattern_option_statuses_ignore_placeholder_arrays_without_usable_state(monkeypatch):
    pattern = SimpleNamespace(
        intensity_meas=[1.0, 2.0],
        intensity_calc=[0.0, 0.0],
        intensity_bkg=[0.0, 0.0],
    )

    experiment = SimpleNamespace(
        type=SimpleNamespace(
            sample_form=SimpleNamespace(value=SampleFormEnum.POWDER.value),
            scattering_type=SimpleNamespace(value=ScatteringTypeEnum.BRAGG.value),
        ),
        linked_phases=[],
        background=[],
        refln=[],
        excluded_regions=[],
    )
    project = SimpleNamespace(
        experiments={'hrpt': experiment},
        structures=SimpleNamespace(names=['phase-a']),
        analysis=SimpleNamespace(fit_results=None),
        rendering=SimpleNamespace(
            plotter=SimpleNamespace(_update_project_categories=lambda expt_name: None),
            chart_engine=SimpleNamespace(value='plotly'),
        ),
    )
    display = ProjectDisplay(project)

    monkeypatch.setattr(
        'easydiffraction.project.display.intensity_category_for', lambda expt: pattern
    )

    statuses = {status.name: status for status in display._pattern_option_statuses('hrpt')}

    assert statuses['measured'].available is True
    assert statuses['calculated'].available is False
    assert statuses['background'].available is False
    assert statuses['bragg'].available is False
    assert statuses['measured'].auto_included is True
    assert statuses['calculated'].auto_included is False


def test_pattern_auto_routes_single_crystal_with_calculated_data(monkeypatch):
    calls: list[tuple[str, tuple, dict]] = []

    def record(name: str):
        def _recorder(*args, **kwargs):
            calls.append((name, args, kwargs))

        return _recorder

    pattern = SimpleNamespace(
        intensity_meas=[10.0, 12.0],
        intensity_calc=[9.5, 11.5],
    )
    experiment = SimpleNamespace(
        type=SimpleNamespace(
            sample_form=SimpleNamespace(value=SampleFormEnum.SINGLE_CRYSTAL.value),
            scattering_type=SimpleNamespace(value=ScatteringTypeEnum.BRAGG.value),
        ),
        linked_crystal=SimpleNamespace(id=SimpleNamespace(value='si')),
        excluded_regions=[],
    )
    project = SimpleNamespace(
        experiments={'heidi': experiment},
        structures=SimpleNamespace(names=['si']),
        analysis=SimpleNamespace(fit_results=None),
        rendering=SimpleNamespace(
            plotter=SimpleNamespace(
                _update_project_categories=lambda expt_name: None,
                _plot_meas_vs_calc_request=record('_plot_meas_vs_calc_request'),
            ),
            chart_engine=SimpleNamespace(value='plotly'),
        ),
    )
    display = ProjectDisplay(project)

    monkeypatch.setattr(
        'easydiffraction.project.display.intensity_category_for',
        lambda expt: pattern,
    )

    display.pattern('heidi')

    assert calls == [
        (
            '_plot_meas_vs_calc_request',
            (),
            {
                'expt_name': 'heidi',
                'plot_options': _MeasVsCalcPlotOptions(
                    x_min=None,
                    x_max=None,
                    show_residual=False,
                    show_background=False,
                    show_bragg=False,
                    show_excluded=False,
                    x=None,
                ),
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
