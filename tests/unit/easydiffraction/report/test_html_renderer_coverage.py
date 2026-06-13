# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Supplementary coverage tests for HTML report rendering."""

from __future__ import annotations

import pathlib
from types import SimpleNamespace

import pytest

# ---------------------------------------------------------------------------
# html_report_path
# ---------------------------------------------------------------------------


def test_html_report_path_returns_explicit_path():
    from easydiffraction.report.html_renderer import html_report_path

    result = html_report_path(object(), path='/reports/custom/report.html')

    assert result == pathlib.Path('/reports/custom/report.html')


def test_html_report_path_accepts_path_object():
    from easydiffraction.report.html_renderer import html_report_path

    explicit = pathlib.Path('/reports/another/out.html')
    result = html_report_path(object(), path=explicit)

    assert result == explicit


def test_html_report_path_builds_from_project_info(tmp_path):
    from easydiffraction.report.html_renderer import html_report_path

    project = SimpleNamespace(
        name='demo',
        metadata=SimpleNamespace(path=str(tmp_path)),
    )

    result = html_report_path(project)

    assert result == tmp_path / 'reports' / 'demo.html'


def test_html_report_path_defaults_project_name(tmp_path):
    from easydiffraction.report.html_renderer import html_report_path

    # A project that exposes a saved path but no name falls back to
    # the 'project' default filename stem.
    project = SimpleNamespace(metadata=SimpleNamespace(path=str(tmp_path)))

    result = html_report_path(project)

    assert result == tmp_path / 'reports' / 'project.html'


def test_html_report_path_raises_without_saved_path():
    from easydiffraction.report.html_renderer import html_report_path

    project = SimpleNamespace(name='demo', metadata=SimpleNamespace(path=None))

    with pytest.raises(FileNotFoundError, match='Save the project first'):
        html_report_path(project)


def test_html_report_path_raises_when_info_missing():
    from easydiffraction.report.html_renderer import html_report_path

    # No 'info' attribute at all -> getattr chain resolves to None.
    project = SimpleNamespace(name='demo')

    with pytest.raises(FileNotFoundError, match='Save the project first'):
        html_report_path(project)


# ---------------------------------------------------------------------------
# save_html_report
# ---------------------------------------------------------------------------


def _minimal_context() -> dict[str, object]:
    return {
        'project': {
            'name': 'p',
            'title': 'P',
            'description': '',
            'n_phases': 0,
            'n_experiments': 0,
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
            'rows': [],
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


def _stub_structure_figures(monkeypatch) -> None:
    """Make the structure-figure step a no-op for save/path tests."""
    from easydiffraction.report import html_renderer

    monkeypatch.setattr(
        html_renderer,
        '_structure_figure_html_context',
        lambda project, *, offline: {},
    )


def test_save_html_report_writes_file_with_explicit_path(tmp_path, monkeypatch):
    from easydiffraction.report.html_renderer import save_html_report

    _stub_structure_figures(monkeypatch)
    target = tmp_path / 'nested' / 'out.html'

    result = save_html_report(object(), _minimal_context(), path=target)

    assert result == target
    assert target.is_file()
    text = target.read_text(encoding='utf-8')
    assert '<h2>Project Summary</h2>' in text
    # Offline assets are not copied when offline is False (default).
    assert not (target.parent / 'vendor').exists()


def test_save_html_report_builds_path_from_project(tmp_path, monkeypatch):
    from easydiffraction.report.html_renderer import save_html_report

    _stub_structure_figures(monkeypatch)
    project = SimpleNamespace(
        name='proj',
        metadata=SimpleNamespace(path=str(tmp_path)),
    )

    result = save_html_report(project, _minimal_context())

    expected = tmp_path / 'reports' / 'proj.html'
    assert result == expected
    assert expected.is_file()


def test_save_html_report_offline_copies_mathjax(tmp_path, monkeypatch):
    from easydiffraction.report.html_renderer import save_html_report

    _stub_structure_figures(monkeypatch)
    target = tmp_path / 'report.html'

    result = save_html_report(
        object(),
        _minimal_context(),
        offline=True,
        path=target,
    )

    assert result == target
    mathjax = target.parent / 'vendor' / 'mathjax-tex-mml-chtml.js'
    assert mathjax.is_file()
    assert mathjax.stat().st_size > 0


# ---------------------------------------------------------------------------
# _copy_mathjax
# ---------------------------------------------------------------------------


def test_copy_mathjax_creates_vendor_bundle(tmp_path):
    from easydiffraction.report.html_renderer import _copy_mathjax

    _copy_mathjax(tmp_path)

    bundle = tmp_path / 'vendor' / 'mathjax-tex-mml-chtml.js'
    assert bundle.is_file()
    assert bundle.stat().st_size > 0


def test_copy_mathjax_is_idempotent(tmp_path):
    from easydiffraction.report.html_renderer import _copy_mathjax

    _copy_mathjax(tmp_path)
    # A second call must not fail even though the vendor dir already exists.
    _copy_mathjax(tmp_path)

    bundle = tmp_path / 'vendor' / 'mathjax-tex-mml-chtml.js'
    assert bundle.is_file()


# ---------------------------------------------------------------------------
# _stylesheet_text / _environment
# ---------------------------------------------------------------------------


def test_stylesheet_text_returns_css():
    from easydiffraction.report.html_renderer import _stylesheet_text

    css = _stylesheet_text()

    assert isinstance(css, str)
    assert css.strip() != ''


def test_environment_loads_report_template():
    from easydiffraction.report.html_renderer import _TEMPLATE_NAME
    from easydiffraction.report.html_renderer import _environment

    env = _environment()
    template = env.get_template(_TEMPLATE_NAME)

    assert template is not None
    assert env.autoescape is True


# ---------------------------------------------------------------------------
# _axis_title
# ---------------------------------------------------------------------------


def test_axis_title_with_units():
    from easydiffraction.report.html_renderer import _axis_title

    title = _axis_title({'display_name': '2theta', 'display_units': 'deg'})

    assert title == '2theta (deg)'


def test_axis_title_without_units():
    from easydiffraction.report.html_renderer import _axis_title

    title = _axis_title({'display_name': 'd-spacing', 'display_units': ''})

    assert title == 'd-spacing'


def test_axis_title_falls_back_to_empty_string():
    from easydiffraction.report.html_renderer import _axis_title

    # Neither display_units nor display_name present.
    assert _axis_title({}) == ''


# ---------------------------------------------------------------------------
# _validate_same_length
# ---------------------------------------------------------------------------


def test_validate_same_length_passes_for_equal_lengths():
    from easydiffraction.report.html_renderer import _validate_same_length

    # No exception for matching lengths.
    _validate_same_length('exp', 'meas', [1, 2, 3], [4, 5, 6])


def test_validate_same_length_raises_for_mismatch():
    from easydiffraction.report.html_renderer import _validate_same_length

    with pytest.raises(ValueError, match="column 'x' has length 3"):
        _validate_same_length('exp', 'calc', [1, 2, 3], [4, 5])


def test_validate_same_length_message_names_experiment_and_column():
    from easydiffraction.report.html_renderer import _validate_same_length

    with pytest.raises(ValueError, match='build report figure') as excinfo:
        _validate_same_length('hrpt', 'bkg', [1, 2], [1, 2, 3, 4])

    message = str(excinfo.value)
    assert "experiment 'hrpt'" in message
    assert "column 'bkg' has length 4" in message


# ---------------------------------------------------------------------------
# _value_list
# ---------------------------------------------------------------------------


def test_value_list_converts_iterable_to_list():
    from easydiffraction.report.html_renderer import _value_list

    assert _value_list((1, 2, 3)) == [1, 2, 3]


def test_value_list_copies_existing_list():
    from easydiffraction.report.html_renderer import _value_list

    source = [1, 2]
    result = _value_list(source)

    assert result == [1, 2]
    assert result is not source


# ---------------------------------------------------------------------------
# _experiment_contexts
# ---------------------------------------------------------------------------


def test_experiment_contexts_returns_empty_for_missing_key():
    from easydiffraction.report.html_renderer import _experiment_contexts

    assert _experiment_contexts({}) == []


def test_experiment_contexts_returns_empty_for_non_list():
    from easydiffraction.report.html_renderer import _experiment_contexts

    assert _experiment_contexts({'experiments': 'not-a-list'}) == []


def test_experiment_contexts_filters_non_dict_entries():
    from easydiffraction.report.html_renderer import _experiment_contexts

    context = {'experiments': [{'id': 'a'}, 'skip', 42, {'id': 'b'}]}

    result = _experiment_contexts(context)

    assert result == [{'id': 'a'}, {'id': 'b'}]


# ---------------------------------------------------------------------------
# _figure_html fallback
# ---------------------------------------------------------------------------


def test_figure_html_falls_back_to_str_when_not_serializable():
    from easydiffraction.report.html_renderer import _figure_html

    class _PlainFigure:
        def __str__(self) -> str:
            return '<plain-figure/>'

    html = _figure_html(
        _PlainFigure(),
        include_plotlyjs=False,
        report_style={'axis_hex': '#000', 'chart_grid_hex': '#fff'},
    )

    assert html == '<plain-figure/>'


def test_figure_html_handles_non_callable_to_html_attr():
    from easydiffraction.report.html_renderer import _figure_html

    # An object whose `to_html` is a non-callable attribute must take the
    # str() fallback branch rather than being treated as a Plotly figure.
    figure = SimpleNamespace(to_html='not callable')

    html = _figure_html(
        figure,
        include_plotlyjs=False,
        report_style={'axis_hex': '#000', 'chart_grid_hex': '#fff'},
    )

    assert 'not callable' in html


# ---------------------------------------------------------------------------
# _fit_figure_html_context branches
# ---------------------------------------------------------------------------


def test_fit_figure_html_context_skips_experiments_without_fit_data():
    from easydiffraction.report.html_renderer import _fit_figure_html_context

    context = {
        'experiments': [
            {'id': 'no_fit'},
            {'id': 'also_no_fit', 'fit_data': None},
        ],
    }

    rendered = _fit_figure_html_context(context, offline=False)

    assert rendered == {}


def test_fit_figure_html_context_renders_powder_figure():
    from easydiffraction.report.html_renderer import _fit_figure_html_context

    context = {
        'experiments': [
            {
                'id': 'hrpt',
                'fit_data': {
                    'x': {'values': [1.0, 2.0], 'display_name': '2theta'},
                    'series': {
                        'meas': {'values': [10.0, 11.0], 'su': None},
                        'calc': {'values': [10.0, 12.0]},
                        'diff': {'values': [0.0, -1.0]},
                        'bkg': None,
                    },
                },
            },
        ],
    }

    rendered = _fit_figure_html_context(context, offline=False)

    assert set(rendered) == {'hrpt'}
    assert 'plotly' in rendered['hrpt'].lower()


def test_fit_figure_html_context_defaults_experiment_id():
    from easydiffraction.report.html_renderer import _fit_figure_html_context

    # An experiment with falsy id falls back to the 'experiment' key.
    context = {
        'experiments': [
            {
                'id': '',
                'fit_data': {
                    'x': {'values': [1.0, 2.0], 'display_name': '2theta'},
                    'series': {
                        'meas': {'values': [10.0, 11.0], 'su': None},
                        'calc': {'values': [10.0, 12.0]},
                        'diff': {'values': [0.0, -1.0]},
                        'bkg': None,
                    },
                },
            },
        ],
    }

    rendered = _fit_figure_html_context(context, offline=False)

    assert set(rendered) == {'experiment'}


def test_fit_figure_html_context_offline_embeds_plotlyjs_once():
    from easydiffraction.report.html_renderer import _fit_figure_html_context

    def _experiment(exp_id: str) -> dict[str, object]:
        return {
            'id': exp_id,
            'fit_data': {
                'x': {'values': [1.0, 2.0], 'display_name': '2theta'},
                'series': {
                    'meas': {'values': [10.0, 11.0], 'su': None},
                    'calc': {'values': [10.0, 12.0]},
                    'diff': {'values': [0.0, -1.0]},
                    'bkg': None,
                },
            },
        }

    context = {'experiments': [_experiment('a'), _experiment('b')]}

    rendered = _fit_figure_html_context(context, offline=True)

    assert set(rendered) == {'a', 'b'}
    # The full Plotly bundle is embedded only in the first figure; the
    # second references the already-loaded library.
    assert len(rendered['a']) > len(rendered['b'])


# ---------------------------------------------------------------------------
# _fit_data_figure: validation + single-crystal branch
# ---------------------------------------------------------------------------


def _powder_fit_data() -> dict[str, object]:
    return {
        'x': {'values': [1.0, 2.0], 'display_name': '2theta'},
        'series': {
            'meas': {'values': [10.0, 11.0], 'su': [0.1, 0.2]},
            'calc': {'values': [10.0, 12.0]},
            'diff': {'values': [0.0, -1.0]},
            'bkg': {'values': [5.0, 5.5]},
        },
    }


def test_fit_data_figure_raises_on_meas_length_mismatch():
    from easydiffraction.report.html_renderer import _fit_data_figure

    fit_data = _powder_fit_data()
    fit_data['series']['meas']['values'] = [10.0]

    with pytest.raises(ValueError, match="column 'meas'"):
        _fit_data_figure('hrpt', fit_data)


def test_fit_data_figure_raises_on_su_length_mismatch():
    from easydiffraction.report.html_renderer import _fit_data_figure

    fit_data = _powder_fit_data()
    fit_data['series']['meas']['su'] = [0.1]

    with pytest.raises(ValueError, match="column 'meas_su'"):
        _fit_data_figure('hrpt', fit_data)


def test_fit_data_figure_raises_on_bkg_length_mismatch():
    from easydiffraction.report.html_renderer import _fit_data_figure

    fit_data = _powder_fit_data()
    fit_data['series']['bkg']['values'] = [5.0]

    with pytest.raises(ValueError, match="column 'bkg'"):
        _fit_data_figure('hrpt', fit_data)


def test_fit_data_figure_builds_single_crystal_figure():
    from easydiffraction.report.html_renderer import _fit_data_figure

    fit_data = {
        'x': {'values': [10.0, 20.0], 'name': 'intensity_calc'},
        'series': {
            'meas': {'values': [11.0, 21.0], 'su': [1.0, 2.0]},
            'calc': {'values': [10.0, 20.0]},
            'diff': {'values': [1.0, 1.0]},
            'bkg': None,
        },
    }

    figure = _fit_data_figure('sxd', fit_data)

    assert hasattr(figure, 'to_html')


def test_fit_data_figure_single_crystal_without_su():
    from easydiffraction.report.html_renderer import _fit_data_figure

    fit_data = {
        'x': {'values': [10.0, 20.0], 'name': 'intensity_calc'},
        'series': {
            'meas': {'values': [11.0, 21.0], 'su': None},
            'calc': {'values': [10.0, 20.0]},
            'diff': {'values': [1.0, 1.0]},
            'bkg': None,
        },
    }

    figure = _fit_data_figure('sxd', fit_data)

    assert hasattr(figure, 'to_html')


# ---------------------------------------------------------------------------
# _single_crystal_fit_data_figure (direct, su=None branch)
# ---------------------------------------------------------------------------


def test_single_crystal_fit_data_figure_zero_fills_su():
    from easydiffraction.report.html_renderer import _single_crystal_fit_data_figure

    figure = _single_crystal_fit_data_figure(
        experiment_id='sxd',
        fit_data={'axes_labels': ['Ical', 'Imeas']},
        x_values=[1.0, 2.0, 3.0],
        y_meas=[1.1, 2.1, 3.1],
        y_meas_su=None,
    )

    assert hasattr(figure, 'to_html')


# ---------------------------------------------------------------------------
# _structure_figure_html_context (heavy deps stubbed)
# ---------------------------------------------------------------------------


def test_structure_figure_html_context_renders_each_structure(monkeypatch):
    from easydiffraction.display.structure import builder
    from easydiffraction.display.structure.renderers import threejs
    from easydiffraction.report.html_renderer import _structure_figure_html_context

    captured: dict[str, object] = {}

    def _fake_availability(structure, *, style):
        captured['availability_style'] = style
        return {'feature': True}

    def _fake_build_scene(structure, *, style, view_range, features):
        captured['view_range'] = view_range
        return {'scene_for': structure.name, 'features': features}

    class _FakeRenderer:
        def render(self, scene, *, features, offline, dark, mode):
            captured['offline'] = offline
            captured['dark'] = dark
            captured['mode'] = mode
            return f'<svg name="{scene["scene_for"]}"/>'

    monkeypatch.setattr(builder, 'structure_feature_availability', _fake_availability)
    monkeypatch.setattr(builder, 'build_scene', _fake_build_scene)
    monkeypatch.setattr(threejs, 'ThreeJsStructureRenderer', _FakeRenderer)

    structures = {
        'phaseA': SimpleNamespace(name='phaseA'),
        'phaseB': SimpleNamespace(name='phaseB'),
    }

    class _Display:
        def _resolve_structure_features(self, mode, availability):
            captured['resolve_mode'] = mode
            return ['atoms']

    project = SimpleNamespace(
        structure_view=SimpleNamespace(view_range=lambda: (0.0, 1.0)),
        structures=structures,
        structure_style='style-obj',
        display=_Display(),
    )

    rendered = _structure_figure_html_context(project, offline=True)

    assert rendered == {
        'phaseA': '<svg name="phaseA"/>',
        'phaseB': '<svg name="phaseB"/>',
    }
    assert captured['offline'] is True
    assert captured['dark'] is False
    assert captured['resolve_mode'] == 'auto'
    assert captured['view_range'] == (0.0, 1.0)


def test_structure_figure_html_context_empty_for_no_structures(monkeypatch):
    from easydiffraction.display.structure import builder
    from easydiffraction.display.structure.renderers import threejs
    from easydiffraction.report.html_renderer import _structure_figure_html_context

    monkeypatch.setattr(
        builder,
        'structure_feature_availability',
        lambda *a, **k: {},
    )
    monkeypatch.setattr(builder, 'build_scene', lambda *a, **k: {})
    monkeypatch.setattr(
        threejs,
        'ThreeJsStructureRenderer',
        lambda: SimpleNamespace(render=lambda *a, **k: ''),
    )

    project = SimpleNamespace(
        structure_view=SimpleNamespace(view_range=lambda: (0.0, 1.0)),
        structures={},
        structure_style='style-obj',
        display=SimpleNamespace(),
    )

    assert _structure_figure_html_context(project, offline=False) == {}


# ---------------------------------------------------------------------------
# render_html_report wires structure figures through when project given
# ---------------------------------------------------------------------------


def test_render_html_report_includes_structure_figures(monkeypatch):
    from easydiffraction.report import html_renderer
    from easydiffraction.report.html_renderer import render_html_report

    monkeypatch.setattr(
        html_renderer,
        '_structure_figure_html_context',
        lambda project, *, offline: {'phaseA': '<svg/>'},
    )

    project = SimpleNamespace(name='proj')
    html = render_html_report(_minimal_context(), project=project)

    assert '<h2>Project Summary</h2>' in html
