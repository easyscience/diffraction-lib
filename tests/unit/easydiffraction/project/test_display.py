# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Unit tests for project/display.py."""

from __future__ import annotations

from contextlib import contextmanager
from types import SimpleNamespace

import pytest

from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum
from easydiffraction.datablocks.structure.item.base import Structure
from easydiffraction.display.progress import ACTIVITY_LABEL_PROCESSING
from easydiffraction.display.plotting import _MeasVsCalcPlotOptions
from easydiffraction.display.structure.builder import FeatureAvailability
from easydiffraction.project.categories.structure_style.default import StructureStyle
from easydiffraction.project.display import PatternOptionStatus
from easydiffraction.project.display import ProjectDisplay
from easydiffraction.utils.enums import VerbosityEnum


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
        plot_all_param_series=record('plot_all_param_series'),
        plot_posterior_pairs=record('plot_posterior_pairs'),
        plot_param_distribution=record('plot_param_distribution'),
        plot_posterior_predictive=record('plot_posterior_predictive'),
        _plot_posterior_predictive_request=record('_plot_posterior_predictive_request'),
        plot_meas=record('plot_meas'),
        plot_calc=record('plot_calc'),
        plot_meas_vs_calc=record('plot_meas_vs_calc'),
        _plot_meas_vs_calc_request=record('_plot_meas_vs_calc_request'),
        engine='plotly',
        _resolve_x_axis=lambda expt_type, x: ('two_theta', 'two_theta', None, None, None),
    )
    project = SimpleNamespace(
        analysis=SimpleNamespace(
            display=analysis_display,
            fit_results=SimpleNamespace(posterior_predictive={}),
            minimizer=SimpleNamespace(_setting_descriptor_names=()),
            bayesian_result=SimpleNamespace(
                has_pair_cache=SimpleNamespace(value=False),
                has_posterior_predictive=SimpleNamespace(value=False),
            ),
            bayesian_pair_caches=[],
            bayesian_predictive_datasets=[],
            _persisted_fit_state_sidecar={},
        ),
        rendering_plot=SimpleNamespace(plotter=plotter),
        experiments={'hrpt': SimpleNamespace(type=SimpleNamespace())},
        free_parameters=[],
        verbosity=SimpleNamespace(fit=SimpleNamespace(value='full')),
    )
    return project, calls


def _make_structure_display_project(structure: object) -> SimpleNamespace:
    return SimpleNamespace(
        structures={'lbco': structure},
        structure_style=StructureStyle(),
        structure_view=SimpleNamespace(
            view_range=lambda: ((0.0, 1.0), (0.0, 1.0), (0.0, 1.0)),
            show_labels=SimpleNamespace(value=False),
            show_moments=SimpleNamespace(value=False),
        ),
        rendering_structure=SimpleNamespace(
            viewer=SimpleNamespace(
                render=lambda scene, *, features: '<html></html>',
                supported_features=lambda: frozenset({'atoms', 'bonds', 'cell', 'axes'}),
            ),
        ),
    )


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


def test_project_display_help_lists_namespaces_and_methods(capsys):
    project, _calls = _make_project_stub()
    display = ProjectDisplay(project)

    display.help()
    out = capsys.readouterr().out

    assert 'parameters' in out
    assert 'fit' in out
    assert 'posterior' in out
    assert 'pattern()' in out
    assert 'show_pattern_options()' in out


def test_nested_project_display_help_lists_methods(capsys):
    project, _calls = _make_project_stub()
    display = ProjectDisplay(project)

    display.parameters.help()
    display.fit.help()
    display.posterior.help()
    out = capsys.readouterr().out

    assert 'all()' in out
    assert 'access()' in out
    assert 'results()' in out
    assert 'correlations()' in out
    assert 'pairs()' in out
    assert 'predictive()' in out


def test_fit_display_delegates_to_analysis_and_chart():
    project, calls = _make_project_stub()
    display = ProjectDisplay(project)

    display.fit.results()
    display.fit.correlations(
        threshold=0.75,
        precision=3,
        max_parameters=4,
        show_diagonal=False,
    )
    display.fit.series(param='scale', versus='diffrn.ambient_temperature')
    display.fit.series(versus='diffrn.ambient_temperature')

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
        {'param': 'scale', 'versus': 'diffrn.ambient_temperature'},
    )
    assert calls[3] == (
        'plot_all_param_series',
        (),
        {'versus': 'diffrn.ambient_temperature'},
    )


def test_posterior_display_delegates_to_chart_plotter(monkeypatch):
    import easydiffraction.project.display as display_mod

    project, calls = _make_project_stub()
    display = ProjectDisplay(project)
    indicator_calls: list[tuple[str, VerbosityEnum]] = []

    @contextmanager
    def fake_activity_indicator(label, *, verbosity):
        indicator_calls.append((label, verbosity))
        yield object()

    monkeypatch.setattr(display_mod, 'activity_indicator', fake_activity_indicator)

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
    assert indicator_calls == [
        (ACTIVITY_LABEL_PROCESSING, VerbosityEnum.FULL),
        (ACTIVITY_LABEL_PROCESSING, VerbosityEnum.FULL),
    ]


def test_posterior_predictive_skips_processing_indicator_for_restored_cache(monkeypatch):
    import easydiffraction.project.display as display_mod

    project, calls = _make_project_stub()
    project.analysis = SimpleNamespace(
        fit_results=object(),
        bayesian_result=SimpleNamespace(has_posterior_predictive=SimpleNamespace(value=True)),
        bayesian_predictive_datasets=[
            SimpleNamespace(
                experiment_name=SimpleNamespace(value='hrpt'),
                x_axis_name=SimpleNamespace(value='two_theta'),
                draws_path=SimpleNamespace(value=None),
            )
        ],
        _persisted_fit_state_sidecar={
            'predictive_datasets': {
                'hrpt': {
                    'x': [1.0, 2.0],
                    'best_sample_prediction': [3.0, 4.0],
                }
            }
        },
    )
    project.experiments = {'hrpt': SimpleNamespace(type=SimpleNamespace())}
    project.rendering_plot.plotter.engine = 'plotly'
    project.rendering_plot.plotter._resolve_x_axis = lambda expt_type, x: (
        'two_theta',
        'two_theta',
        None,
        None,
        None,
    )
    display = ProjectDisplay(project)
    indicator_calls: list[tuple[str, VerbosityEnum]] = []

    @contextmanager
    def fake_activity_indicator(label, *, verbosity):
        indicator_calls.append((label, verbosity))
        yield object()

    monkeypatch.setattr(display_mod, 'activity_indicator', fake_activity_indicator)

    display.posterior.predictive('hrpt')

    assert calls == [
        (
            'plot_posterior_predictive',
            (),
            {
                'expt_name': 'hrpt',
                'style': 'band',
                'x_min': None,
                'x_max': None,
                'show_residual': None,
                'x': None,
            },
        )
    ]
    assert indicator_calls == []


def test_posterior_distribution_without_param_plots_all_free_parameters():
    project, calls = _make_project_stub()
    project.free_parameters = ['a', 'b']
    project.rendering_plot.plotter.engine = 'plotly'
    display = ProjectDisplay(project)

    display.posterior.distribution()

    assert calls == [
        ('plot_param_distribution', ('a',), {}),
        ('plot_param_distribution', ('b',), {}),
    ]


def test_posterior_distribution_without_param_plots_all_free_parameters_for_ascii():
    project, calls = _make_project_stub()
    project.free_parameters = ['a', 'b']
    project.rendering_plot.plotter.engine = 'asciichartpy'
    display = ProjectDisplay(project)

    display.posterior.distribution()

    assert calls == [
        ('plot_param_distribution', ('a',), {}),
        ('plot_param_distribution', ('b',), {}),
    ]


def test_posterior_distribution_without_param_warns_when_no_free_parameters(monkeypatch):
    import easydiffraction.project.display as display_mod

    project, calls = _make_project_stub()
    display = ProjectDisplay(project)
    warnings: list[str] = []

    monkeypatch.setattr(display_mod.log, 'warning', warnings.append)

    display.posterior.distribution()

    assert calls == []
    assert warnings == ['No free parameters found.']


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


def test_pattern_uncertainty_routes_to_posterior_predictive(monkeypatch):
    import easydiffraction.project.display as display_mod

    project, calls = _make_project_stub()
    display = ProjectDisplay(project)
    display._pattern_option_statuses = lambda expt_name: _make_statuses(
        measured=True,
        calculated=True,
        residual=True,
        excluded=True,
        uncertainty=True,
    )
    indicator_calls: list[tuple[str, VerbosityEnum]] = []

    @contextmanager
    def fake_activity_indicator(label, *, verbosity):
        indicator_calls.append((label, verbosity))
        yield object()

    monkeypatch.setattr(display_mod, 'activity_indicator', fake_activity_indicator)

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
    assert indicator_calls == [(ACTIVITY_LABEL_PROCESSING, VerbosityEnum.FULL)]


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
        rendering_plot=SimpleNamespace(
            plotter=SimpleNamespace(_update_project_categories=lambda expt_name: None),
            type='plotly',
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
        rendering_plot=SimpleNamespace(
            plotter=SimpleNamespace(
                _update_project_categories=lambda expt_name: None,
                _plot_meas_vs_calc_request=record('_plot_meas_vs_calc_request'),
            ),
            type='plotly',
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


def test_structure_updates_categories_before_building_scene(monkeypatch, tmp_path):
    structure = Structure(name='lbco')
    structure.space_group.name_h_m = 'P m -3 m'
    structure.cell.length_a = 3.88
    assert structure.cell.length_b.value == 10.0

    project = _make_structure_display_project(structure)
    display = ProjectDisplay(project)
    captured: dict[str, object] = {}

    def fake_build_scene(structure_arg, *, style, view_range, features):
        captured['cell_lengths'] = (
            structure_arg.cell.length_a.value,
            structure_arg.cell.length_b.value,
            structure_arg.cell.length_c.value,
        )
        captured['style'] = style
        captured['view_range'] = view_range
        captured['features'] = features
        return SimpleNamespace()

    monkeypatch.setattr(
        'easydiffraction.display.structure.builder.build_scene',
        fake_build_scene,
    )

    display.structure('lbco', path=str(tmp_path / 'lbco.html'))

    assert captured['cell_lengths'] == pytest.approx((3.88, 3.88, 3.88))
    assert captured['style'] is project.structure_style
    assert captured['view_range'] == ((0.0, 1.0), (0.0, 1.0), (0.0, 1.0))
    assert captured['features'] == frozenset({'cell', 'axes'})


def test_show_structure_options_updates_categories_before_availability(monkeypatch):
    calls: list[str] = []
    structure = SimpleNamespace(updated=False)

    def update_categories():
        calls.append('update')
        structure.updated = True

    def fake_structure_feature_availability(structure_arg, *, style):
        calls.append('availability')
        assert structure_arg.updated is True
        return FeatureAvailability(frozenset({'cell', 'axes'}), ())

    structure._update_categories = update_categories
    project = _make_structure_display_project(structure)
    display = ProjectDisplay(project)

    monkeypatch.setattr(
        'easydiffraction.display.structure.builder.structure_feature_availability',
        fake_structure_feature_availability,
    )
    monkeypatch.setattr('easydiffraction.project.display.render_table', lambda **kwargs: None)

    display.show_structure_options('lbco')

    assert calls == ['update', 'availability']
