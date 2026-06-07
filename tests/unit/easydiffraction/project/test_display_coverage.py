# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Supplementary coverage tests for project/display.py."""

from __future__ import annotations

from contextlib import contextmanager
from types import SimpleNamespace

import pytest

from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum
from easydiffraction.display.progress import ACTIVITY_LABEL_PROCESSING
from easydiffraction.display.structure.builder import FeatureAvailability
from easydiffraction.project.categories.structure_style.default import StructureStyle
from easydiffraction.project.display import PatternOptionStatus
from easydiffraction.project.display import ProjectDisplay
from easydiffraction.utils.enums import VerbosityEnum


def _record(calls: list[tuple[str, tuple, dict]], name: str):
    def _recorder(*args, **kwargs):
        calls.append((name, args, kwargs))

    return _recorder


# ---------------------------------------------------------------------------
# FitDisplay.results / _show_settings_used / _settings_used_rows
# ---------------------------------------------------------------------------


def test_fit_results_with_no_results_skips_settings_table():
    calls: list[tuple[str, tuple, dict]] = []
    project = SimpleNamespace(
        analysis=SimpleNamespace(
            fit_results=None,
            display=SimpleNamespace(fit_results=_record(calls, 'fit_results')),
            minimizer=SimpleNamespace(_setting_descriptor_names=('max_iterations',)),
        ),
    )
    display = ProjectDisplay(project)

    display.fit.results()

    # No fit results -> early return before _show_settings_used touches minimizer.
    assert calls == [('fit_results', (), {})]


def test_fit_results_renders_settings_used_table(monkeypatch):
    import easydiffraction.project.display as display_mod

    calls: list[tuple[str, tuple, dict]] = []
    descriptor = SimpleNamespace(value=42, description='Maximum iterations.')
    project = SimpleNamespace(
        analysis=SimpleNamespace(
            fit_results=object(),
            display=SimpleNamespace(fit_results=_record(calls, 'fit_results')),
            minimizer=SimpleNamespace(
                _setting_descriptor_names=('max_iterations',),
                max_iterations=descriptor,
            ),
        ),
    )
    display = ProjectDisplay(project)

    printed: list[str] = []
    rendered: list[dict] = []
    monkeypatch.setattr(display_mod.console, 'print', printed.append)
    monkeypatch.setattr(display_mod, 'render_table', lambda **kwargs: rendered.append(kwargs))

    display.fit.results()

    assert printed == ['⚙️ Settings used:']
    assert rendered[0]['columns_headers'] == ['Name', 'Value', 'Description']
    assert rendered[0]['columns_data'] == [['max_iterations', '42', 'Maximum iterations.']]
    # The fit table itself is still rendered after the settings table.
    assert calls == [('fit_results', (), {})]


def test_settings_used_rows_uses_empty_string_for_missing_description():
    descriptor = SimpleNamespace(value=0.01, description=None)
    project = SimpleNamespace(
        analysis=SimpleNamespace(
            minimizer=SimpleNamespace(
                _setting_descriptor_names=('tolerance',),
                tolerance=descriptor,
            ),
        ),
    )
    display = ProjectDisplay(project)

    rows = display.fit._settings_used_rows()

    assert rows == [['tolerance', '0.01', '']]


def test_show_settings_used_skips_render_when_no_settings(monkeypatch):
    import easydiffraction.project.display as display_mod

    project = SimpleNamespace(
        analysis=SimpleNamespace(
            minimizer=SimpleNamespace(_setting_descriptor_names=()),
        ),
    )
    display = ProjectDisplay(project)

    printed: list[str] = []
    rendered: list[dict] = []
    monkeypatch.setattr(display_mod.console, 'print', printed.append)
    monkeypatch.setattr(display_mod, 'render_table', lambda **kwargs: rendered.append(kwargs))

    display.fit._show_settings_used()

    assert printed == []
    assert rendered == []


# ---------------------------------------------------------------------------
# PosteriorDisplay._pairs_need_processing_indicator
# ---------------------------------------------------------------------------


def _posterior_display(project: object):
    return ProjectDisplay(project).posterior


def test_pairs_indicator_required_when_parameters_given():
    project = SimpleNamespace(analysis=SimpleNamespace())
    posterior = _posterior_display(project)

    assert posterior._pairs_need_processing_indicator(parameters=['a']) is True


def test_pairs_indicator_skipped_when_runtime_pair_caches_present():
    project = SimpleNamespace(
        analysis=SimpleNamespace(
            fit_results=SimpleNamespace(posterior_pair_caches={'a:b': object()}),
        ),
    )
    posterior = _posterior_display(project)

    assert posterior._pairs_need_processing_indicator(parameters=None) is False


def test_pairs_indicator_skipped_when_sidecar_pair_caches_present():
    project = SimpleNamespace(
        analysis=SimpleNamespace(
            fit_results=SimpleNamespace(posterior_pair_caches=None),
            _persisted_fit_state_sidecar={'pair_caches': {'a:b': {}}},
        ),
    )
    posterior = _posterior_display(project)

    assert posterior._pairs_need_processing_indicator(parameters=None) is False


def test_pairs_indicator_required_when_no_caches_anywhere():
    project = SimpleNamespace(
        analysis=SimpleNamespace(
            fit_results=SimpleNamespace(posterior_pair_caches=None),
            _persisted_fit_state_sidecar={},
        ),
    )
    posterior = _posterior_display(project)

    assert posterior._pairs_need_processing_indicator(parameters=None) is True


def test_pairs_uses_nullcontext_when_indicator_not_needed(monkeypatch):
    import easydiffraction.project.display as display_mod

    calls: list[tuple[str, tuple, dict]] = []
    project = SimpleNamespace(
        analysis=SimpleNamespace(
            fit_results=SimpleNamespace(posterior_pair_caches={'a:b': object()}),
        ),
        rendering_plot=SimpleNamespace(
            plotter=SimpleNamespace(plot_posterior_pairs=_record(calls, 'plot_posterior_pairs')),
        ),
        verbosity=SimpleNamespace(fit=SimpleNamespace(value='full')),
    )
    posterior = _posterior_display(project)

    indicator_calls: list[object] = []

    @contextmanager
    def fake_activity_indicator(label, *, verbosity):
        indicator_calls.append(label)
        yield object()

    monkeypatch.setattr(display_mod, 'activity_indicator', fake_activity_indicator)

    posterior.pairs()

    assert calls[0][0] == 'plot_posterior_pairs'
    # Cache present -> nullcontext is used, indicator never created.
    assert indicator_calls == []


# ---------------------------------------------------------------------------
# PosteriorDisplay._predictive_needs_processing_indicator
# ---------------------------------------------------------------------------


def _predictive_project(*, sidecar, fit_results, engine='plotly'):
    plotter = SimpleNamespace(
        engine=engine,
        _resolve_x_axis=lambda expt_type, x: ('two_theta', 'two_theta', None, None, None),
    )
    return SimpleNamespace(
        analysis=SimpleNamespace(
            fit_results=fit_results,
            _persisted_fit_state_sidecar=sidecar,
        ),
        experiments={'hrpt': SimpleNamespace(type=SimpleNamespace())},
        rendering_plot=SimpleNamespace(plotter=plotter),
    )


def test_predictive_indicator_sidecar_axis_mismatch_falls_through_to_results():
    # Sidecar dataset exists but for a different axis -> ignored; fit_results
    # posterior_predictive empty -> processing required.
    project = _predictive_project(
        sidecar={'predictive_datasets': {'hrpt': {'x_axis_name': 'd_spacing'}}},
        fit_results=SimpleNamespace(posterior_predictive={}),
    )
    posterior = _posterior_display(project)

    needs = posterior._predictive_needs_processing_indicator(
        expt_name='hrpt',
        style='band',
        x=None,
    )

    assert needs is True


def test_predictive_indicator_sidecar_band_style_complete():
    # Matching-axis sidecar dataset and band style -> no draws required ->
    # processing already done.
    project = _predictive_project(
        sidecar={'predictive_datasets': {'hrpt': {'x_axis_name': 'two_theta', 'draws': None}}},
        fit_results=SimpleNamespace(posterior_predictive={}),
    )
    posterior = _posterior_display(project)

    needs = posterior._predictive_needs_processing_indicator(
        expt_name='hrpt',
        style='band',
        x=None,
    )

    assert needs is False


def test_predictive_indicator_sidecar_draws_style_missing_draws():
    # Plotly + draws style needs draws; sidecar dataset has none -> required.
    project = _predictive_project(
        sidecar={'predictive_datasets': {'hrpt': {'x_axis_name': '', 'draws': None}}},
        fit_results=SimpleNamespace(posterior_predictive={}),
    )
    posterior = _posterior_display(project)

    needs = posterior._predictive_needs_processing_indicator(
        expt_name='hrpt',
        style='draws',
        x=None,
    )

    assert needs is True


def test_predictive_indicator_runtime_cache_band_complete():
    # No sidecar; fit_results cache keyed on band axis with matching axis name
    # and band style -> no draws needed -> processing complete.
    summary = SimpleNamespace(x_axis_name='two_theta', draws=None)
    project = _predictive_project(
        sidecar={},
        fit_results=SimpleNamespace(
            posterior_predictive={'hrpt:two_theta:band': summary},
        ),
    )
    posterior = _posterior_display(project)

    needs = posterior._predictive_needs_processing_indicator(
        expt_name='hrpt',
        style='band',
        x=None,
    )

    assert needs is False


def test_predictive_indicator_runtime_cache_axis_mismatch_then_exhausted():
    # Cache entry exists but its x_axis_name disagrees -> skip; remaining keys
    # absent -> fall through to required.
    summary = SimpleNamespace(x_axis_name='d_spacing', draws=None)
    project = _predictive_project(
        sidecar={},
        fit_results=SimpleNamespace(
            posterior_predictive={'hrpt:two_theta:band': summary},
        ),
    )
    posterior = _posterior_display(project)

    needs = posterior._predictive_needs_processing_indicator(
        expt_name='hrpt',
        style='band',
        x=None,
    )

    assert needs is True


def test_predictive_indicator_no_posterior_predictive_requires_processing():
    project = _predictive_project(
        sidecar={},
        fit_results=SimpleNamespace(posterior_predictive=None),
    )
    posterior = _posterior_display(project)

    needs = posterior._predictive_needs_processing_indicator(
        expt_name='hrpt',
        style='band',
        x=None,
    )

    assert needs is True


# ---------------------------------------------------------------------------
# ProjectDisplay.structure (display path) + _emit_structure_output
# ---------------------------------------------------------------------------


def _structure_display_project(structure, *, engine='ascii', render_output='<html></html>'):
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
                engine=engine,
                render=lambda scene, *, features: render_output,
                supported_features=lambda: frozenset({'atoms', 'bonds', 'cell', 'axes'}),
            ),
        ),
    )


def test_structure_display_path_prints_ascii_output(monkeypatch, capsys):
    structure = SimpleNamespace(_update_categories=lambda: None)
    project = _structure_display_project(structure, engine='ascii', render_output='ASCII-VIEW')
    display = ProjectDisplay(project)

    monkeypatch.setattr(
        'easydiffraction.display.structure.builder.build_scene',
        lambda *a, **k: SimpleNamespace(),
    )
    monkeypatch.setattr(
        'easydiffraction.display.structure.builder.structure_feature_availability',
        lambda structure_arg, *, style: FeatureAvailability(frozenset({'cell', 'axes'}), ()),
    )

    display.structure('lbco')

    out = capsys.readouterr().out
    # Paragraph header from console.paragraph plus the raw ASCII view via print().
    assert 'Structure' in out
    assert 'ASCII-VIEW' in out


def test_emit_structure_output_ascii_uses_print(capsys):
    project = _structure_display_project(
        SimpleNamespace(_update_categories=lambda: None), engine='ascii'
    )
    display = ProjectDisplay(project)

    display._emit_structure_output('RAW\x1b[0mANSI')

    out = capsys.readouterr().out
    assert 'RAW\x1b[0mANSI' in out


def test_emit_structure_output_threejs_terminal_hint(monkeypatch):
    import easydiffraction.project.display as display_mod

    project = _structure_display_project(
        SimpleNamespace(_update_categories=lambda: None), engine='threejs'
    )
    display = ProjectDisplay(project)

    monkeypatch.setattr(
        'easydiffraction.utils.environment.in_jupyter',
        lambda: False,
    )
    printed: list[str] = []
    monkeypatch.setattr(display_mod.console, 'print', printed.append)

    display._emit_structure_output('<html></html>')

    assert len(printed) == 1
    assert 'Three.js structure view generated as HTML' in printed[0]


def test_emit_structure_output_threejs_in_jupyter_displays_html(monkeypatch):
    import sys
    import types

    project = _structure_display_project(
        SimpleNamespace(_update_categories=lambda: None), engine='threejs'
    )
    display = ProjectDisplay(project)

    monkeypatch.setattr(
        'easydiffraction.utils.environment.in_jupyter',
        lambda: True,
    )

    displayed: list[object] = []
    fake_ipython_display = types.ModuleType('IPython.display')
    fake_ipython_display.HTML = lambda html: ('HTML', html)
    fake_ipython_display.display = displayed.append
    fake_ipython = types.ModuleType('IPython')
    fake_ipython.display = fake_ipython_display
    monkeypatch.setitem(sys.modules, 'IPython', fake_ipython)
    monkeypatch.setitem(sys.modules, 'IPython.display', fake_ipython_display)

    display._emit_structure_output('<div>view</div>')

    assert displayed == [('HTML', '<div>view</div>')]


# ---------------------------------------------------------------------------
# show_structure_options radius substitutions
# ---------------------------------------------------------------------------


def test_show_structure_options_reports_radius_substitutions(monkeypatch):
    import easydiffraction.project.display as display_mod

    structure = SimpleNamespace(_update_categories=lambda: None)
    project = _structure_display_project(structure)
    display = ProjectDisplay(project)

    monkeypatch.setattr(
        'easydiffraction.display.structure.builder.structure_feature_availability',
        lambda structure_arg, *, style: FeatureAvailability(
            frozenset({'cell', 'axes'}), ('Xx', 'Yy')
        ),
    )
    monkeypatch.setattr(display_mod, 'render_table', lambda **kwargs: None)
    paragraphs: list[str] = []
    printed: list[str] = []
    monkeypatch.setattr(display_mod.console, 'paragraph', paragraphs.append)
    monkeypatch.setattr(display_mod.console, 'print', printed.append)

    display.show_structure_options('lbco')

    assert paragraphs == ['Radius substitutions (fell back to covalent)']
    assert printed == ['Xx, Yy']


# ---------------------------------------------------------------------------
# _resolve_structure_features + _normalize_structure_include
# ---------------------------------------------------------------------------


def _resolver_project(*, show_labels=False, show_moments=False):
    return SimpleNamespace(
        structure_view=SimpleNamespace(
            show_labels=SimpleNamespace(value=show_labels),
            show_moments=SimpleNamespace(value=show_moments),
        ),
    )


def test_resolve_features_explicit_tuple_wins():
    display = ProjectDisplay(_resolver_project())
    availability = FeatureAvailability(frozenset({'atoms', 'cell'}), ())

    resolved = display._resolve_structure_features(('atoms', 'bonds'), availability)

    # Explicit include bypasses availability filtering.
    assert resolved == frozenset({'atoms', 'bonds'})


def test_resolve_features_auto_adds_labels_and_moments_when_enabled():
    display = ProjectDisplay(_resolver_project(show_labels=True, show_moments=True))
    availability = FeatureAvailability(
        frozenset({'atoms', 'bonds', 'cell', 'axes', 'labels', 'moments'}), ()
    )

    resolved = display._resolve_structure_features('auto', availability)

    assert resolved == frozenset({'atoms', 'bonds', 'cell', 'axes', 'labels', 'moments'})


def test_resolve_features_auto_omits_labels_moments_when_disabled():
    display = ProjectDisplay(_resolver_project(show_labels=False, show_moments=False))
    availability = FeatureAvailability(frozenset({'atoms', 'cell', 'labels', 'moments'}), ())

    resolved = display._resolve_structure_features('auto', availability)

    assert resolved == frozenset({'atoms', 'cell'})


def test_normalize_structure_include_rejects_empty_tuple():
    with pytest.raises(ValueError, match='at least one option'):
        ProjectDisplay._normalize_structure_include(())


def test_normalize_structure_include_rejects_unknown_options():
    with pytest.raises(ValueError, match='Unknown structure include option'):
        ProjectDisplay._normalize_structure_include(('atoms', 'sparkles'))


def test_normalize_structure_include_rejects_auto_with_others():
    with pytest.raises(ValueError, match="'auto' cannot be combined"):
        ProjectDisplay._normalize_structure_include(('auto', 'atoms'))


def test_normalize_structure_include_dedupes_preserving_order():
    normalized = ProjectDisplay._normalize_structure_include(('atoms', 'atoms', 'cell'))

    assert normalized == ('atoms', 'cell')


# ---------------------------------------------------------------------------
# _status_by_name
# ---------------------------------------------------------------------------


def _status(name: str, *, available: bool = True, auto_included: bool = False):
    return PatternOptionStatus(
        name=name,
        description=name,
        available=available,
        auto_included=auto_included,
        reason='',
    )


def test_status_by_name_returns_matching_status():
    statuses = [
        _status('auto', auto_included=True),
        _status('measured'),
    ]

    found = ProjectDisplay._status_by_name(statuses, 'measured')

    assert found.name == 'measured'


def test_status_by_name_raises_for_unknown_option():
    statuses = [_status('auto', auto_included=True)]

    with pytest.raises(ValueError, match='Unknown pattern option: bragg'):
        ProjectDisplay._status_by_name(statuses, 'bragg')


# ---------------------------------------------------------------------------
# _show_point_estimate_pattern dispatch (calculated branches + error)
# ---------------------------------------------------------------------------


def _point_estimate_display():
    calls: list[tuple[str, tuple, dict]] = []
    plotter = SimpleNamespace(
        plot_meas=_record(calls, 'plot_meas'),
        plot_calc=_record(calls, 'plot_calc'),
        _plot_meas_vs_calc_request=_record(calls, '_plot_meas_vs_calc_request'),
    )
    project = SimpleNamespace(rendering_plot=SimpleNamespace(plotter=plotter))
    return ProjectDisplay(project), calls


def test_point_estimate_calculated_only_routes_to_plot_calc():
    display, calls = _point_estimate_display()

    display._show_point_estimate_pattern(
        expt_name='hrpt',
        x_min=None,
        x_max=None,
        include=('calculated',),
        x=None,
    )

    assert calls == [
        (
            'plot_calc',
            (),
            {
                'expt_name': 'hrpt',
                'x_min': None,
                'x_max': None,
                'x': None,
                'show_excluded': False,
            },
        )
    ]


def test_point_estimate_calculated_and_excluded_shades_region():
    display, calls = _point_estimate_display()

    display._show_point_estimate_pattern(
        expt_name='hrpt',
        x_min=1.0,
        x_max=5.0,
        include=('calculated', 'excluded'),
        x=None,
    )

    assert calls == [
        (
            'plot_calc',
            (),
            {
                'expt_name': 'hrpt',
                'x_min': 1.0,
                'x_max': 5.0,
                'x': None,
                'show_excluded': True,
            },
        )
    ]


def test_point_estimate_unsupported_combination_raises():
    display, _calls = _point_estimate_display()

    with pytest.raises(ValueError, match="'measured', 'calculated', or combinations"):
        display._show_point_estimate_pattern(
            expt_name='hrpt',
            x_min=None,
            x_max=None,
            include=('background',),
            x=None,
        )


def test_pattern_auto_routes_calculated_only_to_plot_calc():
    display, calls = _point_estimate_display()
    display._pattern_option_statuses = lambda expt_name: _calculated_only_statuses()

    display.pattern('hrpt')

    assert calls[0][0] == 'plot_calc'
    assert calls[0][2]['show_excluded'] is False


def _calculated_only_statuses() -> list[PatternOptionStatus]:
    return [
        _status('auto', auto_included=True),
        _status('measured', available=False),
        _status('calculated', available=True),
        _status('background', available=False),
        _status('residual', available=False),
        _status('bragg', available=False),
        _status('excluded', available=False),
        _status('uncertainty', available=False),
    ]


# ---------------------------------------------------------------------------
# _has_nonempty_value
# ---------------------------------------------------------------------------


def test_has_nonempty_value_none_is_empty():
    assert ProjectDisplay._has_nonempty_value(None) is False


def test_has_nonempty_value_empty_sequence():
    assert ProjectDisplay._has_nonempty_value([]) is False


def test_has_nonempty_value_nonempty_sequence():
    assert ProjectDisplay._has_nonempty_value([1, 2]) is True


def test_has_nonempty_value_unsized_object_is_nonempty():
    # Objects without __len__ raise TypeError internally and are treated as present.
    assert ProjectDisplay._has_nonempty_value(object()) is True


# ---------------------------------------------------------------------------
# _has_linked_structure_for_calculation
# ---------------------------------------------------------------------------


def _linked_display(structure_names):
    project = SimpleNamespace(structures=SimpleNamespace(names=structure_names))
    return ProjectDisplay(project)


def test_linked_structure_matches_via_linked_phases():
    display = _linked_display(['phase-a'])
    linked_phase = SimpleNamespace(
        _identity=SimpleNamespace(category_entry_name='phase-a'),
    )
    experiment = SimpleNamespace(linked_phases=[linked_phase])

    assert display._has_linked_structure_for_calculation(experiment) is True


def test_linked_structure_phases_present_but_no_match_falls_to_crystal():
    display = _linked_display(['phase-a'])
    linked_phase = SimpleNamespace(
        _identity=SimpleNamespace(category_entry_name='other'),
    )
    experiment = SimpleNamespace(
        linked_phases=[linked_phase],
        linked_crystal=SimpleNamespace(id=SimpleNamespace(value='phase-a')),
    )

    # No phase matched, but linked_crystal id does.
    assert display._has_linked_structure_for_calculation(experiment) is True


def test_linked_structure_no_match_anywhere():
    display = _linked_display(['phase-a'])
    experiment = SimpleNamespace(
        linked_phases=[],
        linked_crystal=SimpleNamespace(id=SimpleNamespace(value='missing')),
    )

    assert display._has_linked_structure_for_calculation(experiment) is False


# ---------------------------------------------------------------------------
# _uncertainty_status
# ---------------------------------------------------------------------------


def _uncertainty_display(*, fit_results=None, engine='plotly', plotter_type='plotly'):
    plotter = SimpleNamespace()
    if engine is not None:
        plotter.engine = engine
    project = SimpleNamespace(
        analysis=SimpleNamespace(fit_results=fit_results),
        rendering_plot=SimpleNamespace(plotter=plotter, type=plotter_type),
    )
    return ProjectDisplay(project)


def test_uncertainty_status_requires_measured_data():
    display = _uncertainty_display()

    available, reason = display._uncertainty_status(
        measured_available=False,
        sample_form=SampleFormEnum.POWDER.value,
        scattering_type=ScatteringTypeEnum.BRAGG.value,
    )

    assert available is False
    assert reason == 'Uncertainty bands require measured data.'


def test_uncertainty_status_rejects_unsupported_sample_form():
    display = _uncertainty_display()

    available, reason = display._uncertainty_status(
        measured_available=True,
        sample_form=SampleFormEnum.SINGLE_CRYSTAL.value,
        scattering_type=ScatteringTypeEnum.TOTAL.value,
    )

    assert available is False
    assert 'unavailable for this experiment type' in reason


def test_uncertainty_status_requires_fit_results():
    display = _uncertainty_display(fit_results=None)

    available, reason = display._uncertainty_status(
        measured_available=True,
        sample_form=SampleFormEnum.POWDER.value,
        scattering_type=ScatteringTypeEnum.BRAGG.value,
    )

    assert available is False
    assert reason == 'No fit results are available.'


def test_uncertainty_status_requires_posterior_predictive():
    display = _uncertainty_display(
        fit_results=SimpleNamespace(posterior_predictive={}),
    )

    available, reason = display._uncertainty_status(
        measured_available=True,
        sample_form=SampleFormEnum.POWDER.value,
        scattering_type=ScatteringTypeEnum.BRAGG.value,
    )

    assert available is False
    assert reason == 'Posterior predictive data is unavailable.'


def test_uncertainty_status_requires_plotly_engine():
    display = _uncertainty_display(
        fit_results=SimpleNamespace(posterior_predictive={'k': object()}),
        engine='asciichartpy',
    )

    available, reason = display._uncertainty_status(
        measured_available=True,
        sample_form=SampleFormEnum.POWDER.value,
        scattering_type=ScatteringTypeEnum.BRAGG.value,
    )

    assert available is False
    assert 'require the Plotly chart engine' in reason


def test_uncertainty_status_available_for_powder_plotly():
    display = _uncertainty_display(
        fit_results=SimpleNamespace(posterior_predictive={'k': object()}),
        engine='plotly',
    )

    available, reason = display._uncertainty_status(
        measured_available=True,
        sample_form=SampleFormEnum.POWDER.value,
        scattering_type=ScatteringTypeEnum.BRAGG.value,
    )

    assert available is True
    assert reason == ''


def test_uncertainty_status_single_crystal_bragg_uses_rendering_type_fallback():
    # plotter has no ``engine`` attribute -> falls back to rendering_plot.type.
    display = _uncertainty_display(
        fit_results=SimpleNamespace(posterior_predictive={'k': object()}),
        engine=None,
        plotter_type='plotly',
    )

    available, reason = display._uncertainty_status(
        measured_available=True,
        sample_form=SampleFormEnum.SINGLE_CRYSTAL.value,
        scattering_type=ScatteringTypeEnum.BRAGG.value,
    )

    assert available is True
    assert reason == ''


# ---------------------------------------------------------------------------
# pairs() indicator path (covers activity_indicator branch end-to-end)
# ---------------------------------------------------------------------------


def test_pairs_uses_indicator_when_processing_needed(monkeypatch):
    import easydiffraction.project.display as display_mod

    calls: list[tuple[str, tuple, dict]] = []
    project = SimpleNamespace(
        analysis=SimpleNamespace(
            fit_results=SimpleNamespace(posterior_pair_caches=None),
            _persisted_fit_state_sidecar={},
        ),
        rendering_plot=SimpleNamespace(
            plotter=SimpleNamespace(plot_posterior_pairs=_record(calls, 'plot_posterior_pairs')),
        ),
        verbosity=SimpleNamespace(fit=SimpleNamespace(value='full')),
    )
    posterior = _posterior_display(project)

    indicator_calls: list[tuple[str, VerbosityEnum]] = []

    @contextmanager
    def fake_activity_indicator(label, *, verbosity):
        indicator_calls.append((label, verbosity))
        yield object()

    monkeypatch.setattr(display_mod, 'activity_indicator', fake_activity_indicator)

    posterior.pairs()

    assert calls[0][0] == 'plot_posterior_pairs'
    assert indicator_calls == [(ACTIVITY_LABEL_PROCESSING, VerbosityEnum.FULL)]
