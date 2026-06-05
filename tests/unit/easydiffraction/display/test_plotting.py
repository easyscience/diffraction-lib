# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

import csv
import re
from types import MethodType
from types import SimpleNamespace

import numpy as np
import pytest


def _strip_markup(text: str) -> str:
    """Remove Rich color markup tags like [red]...[/red]."""
    return re.sub(r'\[(\w+)\](.*?)\[/\1\]', r'\2', text)


def test_module_import():
    import easydiffraction.display.plotting as MUT

    expected_module_name = 'easydiffraction.display.plotting'
    actual_module_name = MUT.__name__
    assert expected_module_name == actual_module_name


def test_plotter_configuration_and_engine_switch(capsys):
    from easydiffraction.display.plotting import Plotter

    p = Plotter()
    # show config prints a table
    p.show_config()
    out1 = capsys.readouterr().out
    assert 'Current plotter configuration' in out1

    # show supported engines prints a table (now via base RendererBase title)
    p.show_supported_engines()
    out2 = capsys.readouterr().out
    # assert 'Supported plotter engines' in out2
    assert 'Supported engines' in out2

    # Switch engine to its current value (no-op, but exercise setter)
    cur = p.engine
    p.engine = cur
    # And to an unsupported engine (prints error and leaves engine unchanged)
    p.engine = '___not_supported___'
    assert p.engine == cur

    # Supported engines include both known backends
    p.show_supported_engines()
    out3 = capsys.readouterr().out
    assert 'asciichartpy' in out3 or 'plotly' in out3


def test_plotter_factory_supported_and_unsupported():
    from easydiffraction.display.plotting import PlotterFactory

    # Supported engine creates a backend instance
    obj = PlotterFactory.create('asciichartpy')
    assert obj is not None

    # Unsupported engine should raise ValueError (unified policy)
    with pytest.raises(
        ValueError,
        match=r"Unsupported engine 'nope'\. Supported engines: .*",
    ):
        PlotterFactory.create('nope')


@pytest.mark.parametrize(
    ('descriptor_name', 'column_values', 'expected_y'),
    [
        ('reduced_chi_square', ['1.5', '2.5'], [1.5, 2.5]),
        ('iterations', ['5', '8'], [5.0, 8.0]),
        ('success', ['True', 'False'], [1.0, 0.0]),
    ],
)
def test_plot_param_series_reads_fit_result_columns_from_csv(
    monkeypatch,
    tmp_path,
    descriptor_name,
    column_values,
    expected_y,
):
    from easydiffraction.display.plotting import Plotter
    from easydiffraction.project.project import Project

    project = Project(name='series')
    project.info.path = tmp_path

    analysis_dir = tmp_path / 'analysis'
    analysis_dir.mkdir(parents=True)
    csv_path = analysis_dir / 'results.csv'
    with csv_path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                'file_path',
                'fit_result.reduced_chi_square',
                'fit_result.success',
                'fit_result.iterations',
            ],
        )
        writer.writeheader()
        writer.writerow({
            'file_path': 'a.dat',
            'fit_result.reduced_chi_square': column_values[0],
            'fit_result.success': column_values[0] if descriptor_name == 'success' else 'True',
            'fit_result.iterations': column_values[0] if descriptor_name == 'iterations' else '5',
        })
        writer.writerow({
            'file_path': 'b.dat',
            'fit_result.reduced_chi_square': column_values[1],
            'fit_result.success': column_values[1] if descriptor_name == 'success' else 'False',
            'fit_result.iterations': column_values[1] if descriptor_name == 'iterations' else '8',
        })

    captured: dict[str, object] = {}

    plotter = Plotter()
    plotter._set_project(project)

    def fake_plot_scatter(*, x, y, sy, axes_labels, title, height):
        captured['x'] = x
        captured['y'] = y
        captured['sy'] = sy
        captured['axes_labels'] = axes_labels
        captured['title'] = title
        captured['height'] = height

    monkeypatch.setattr(plotter._backend, 'plot_scatter', fake_plot_scatter)

    plotter.plot_param_series(getattr(project.analysis.fit_result, descriptor_name))

    assert captured['x'] == [1, 2]
    assert captured['y'] == expected_y
    assert captured['sy'] == [0.0, 0.0]
    assert captured['axes_labels'] == ['Experiment No.', 'Parameter value']
    assert captured['title'] == f"Parameter 'fit_result.{descriptor_name}' across fit results"


def test_plotter_error_paths_and_filtering(capsys, monkeypatch):
    from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
    from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
    from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum
    from easydiffraction.display.plotting import Plotter
    from easydiffraction.display.plotting import _MeasVsCalcPlotOptions
    from easydiffraction.utils.logging import Logger

    monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)

    class Ptn:
        def __init__(
            self, two_theta=None, intensity_meas=None, intensity_calc=None, d_spacing=None
        ):
            self.two_theta = two_theta
            self.intensity_meas = intensity_meas
            self.intensity_calc = intensity_calc
            self.d_spacing = d_spacing if d_spacing is not None else two_theta

    class ExptType:
        def __init__(self):
            self.sample_form = type('SF', (), {'value': SampleFormEnum.POWDER})
            self.scattering_type = type('S', (), {'value': ScatteringTypeEnum.BRAGG})
            self.beam_mode = type('B', (), {'value': BeamModeEnum.CONSTANT_WAVELENGTH})

    p = Plotter()

    # Error paths (now log errors via console; messages are printed)
    p._plot_meas_data(
        object(),
        Ptn(two_theta=None, intensity_meas=None),
        'E',
        ExptType(),
        _MeasVsCalcPlotOptions(),
    )
    out = capsys.readouterr().out
    assert 'No two_theta data available for experiment E' in out

    p._plot_meas_data(
        object(),
        Ptn(two_theta=[1], intensity_meas=None),
        'E',
        ExptType(),
        _MeasVsCalcPlotOptions(),
    )
    out = capsys.readouterr().out
    assert 'No measured data available for experiment E' in out

    p._plot_calc_data(
        object(),
        Ptn(two_theta=None, intensity_calc=None),
        'E',
        ExptType(),
        _MeasVsCalcPlotOptions(),
    )
    out = capsys.readouterr().out
    assert 'No two_theta data available for experiment E' in out

    p._plot_calc_data(
        object(),
        Ptn(two_theta=[1], intensity_calc=None),
        'E',
        ExptType(),
        _MeasVsCalcPlotOptions(),
    )
    out = capsys.readouterr().out
    assert 'No calculated data available for experiment E' in out

    class Expt:
        def __init__(self, pattern, expt_type):
            self.data = pattern
            self.type = expt_type

    p._plot_meas_vs_calc_data(
        Expt(Ptn(two_theta=None, intensity_meas=None, intensity_calc=None), ExptType()),
        'E',
        _MeasVsCalcPlotOptions(),
    )
    out = capsys.readouterr().out
    assert 'No measured data available for experiment E' in out
    p._plot_meas_vs_calc_data(
        Expt(Ptn(two_theta=[1], intensity_meas=None, intensity_calc=[1]), ExptType()),
        'E',
        _MeasVsCalcPlotOptions(),
    )
    out = capsys.readouterr().out
    assert 'No measured data available for experiment E' in out
    p._plot_meas_vs_calc_data(
        Expt(Ptn(two_theta=[1], intensity_meas=[1], intensity_calc=None), ExptType()),
        'E',
        _MeasVsCalcPlotOptions(),
    )
    out = capsys.readouterr().out
    assert 'No calculated data available for experiment E' in out

    # Filtering
    import numpy as np

    p.x_min, p.x_max = 0.5, 1.5
    arr = np.array([0.0, 1.0, 2.0])
    filt = p._filtered_y_array(arr, arr, None, None)
    assert np.allclose(filt, np.array([1.0]))


def test_plotter_routes_to_ascii_plotter(monkeypatch):
    import numpy as np

    import easydiffraction.display.plotters.ascii as ascii_mod
    from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
    from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
    from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum
    from easydiffraction.display.plotting import Plotter
    from easydiffraction.display.plotting import _MeasVsCalcPlotOptions

    called = {}

    def fake_plot_powder(
        self,
        x,
        y_series,
        labels,
        axes_labels,
        title,
        height=None,
        excluded_ranges=(),
    ):
        called['labels'] = tuple(labels)
        called['axes'] = tuple(axes_labels)
        called['title'] = title
        called['excluded_ranges'] = excluded_ranges

    monkeypatch.setattr(ascii_mod.AsciiPlotter, 'plot_powder', fake_plot_powder)

    class Ptn:
        def __init__(self):
            self.two_theta = np.array([0.0, 1.0])
            self.intensity_meas = np.array([1.0, 2.0])
            self.intensity_calc = np.array([1.0, 2.0])
            self.d_spacing = self.two_theta

    class ExptType:
        def __init__(self):
            self.sample_form = type('SF', (), {'value': SampleFormEnum.POWDER})
            self.scattering_type = type('S', (), {'value': ScatteringTypeEnum.BRAGG})
            self.beam_mode = type('B', (), {'value': BeamModeEnum.CONSTANT_WAVELENGTH})

    p = Plotter()
    p.engine = 'asciichartpy'  # ensure AsciiPlotter
    p._plot_meas_data(
        object(),
        Ptn(),
        'E',
        ExptType(),
        _MeasVsCalcPlotOptions(),
    )
    assert called['labels'] == ('meas',)
    assert called['title'] == "Diffraction pattern for experiment 🔬 'E'"
    assert called['excluded_ranges'] == ()

    p._plot_calc_data(
        object(),
        Ptn(),
        'E',
        ExptType(),
        _MeasVsCalcPlotOptions(),
    )
    assert called['labels'] == ('calc',)
    assert called['title'] == "Diffraction pattern for experiment 🔬 'E'"
    assert called['excluded_ranges'] == ()


def test_extract_bragg_tick_sets_groups_and_filters():
    import numpy as np

    from easydiffraction.display.plotting import Plotter
    from easydiffraction.display.plotting import XAxisType

    class Refln:
        phase_id = np.array(['phase-a', 'phase-a', 'phase-b', 'phase-b'])
        two_theta = np.array([0.5, 1.5, 2.5, 3.5])
        index_h = np.array([1, 2, 3, 4])
        index_k = np.array([0, 1, 1, 2])
        index_l = np.array([1, 0, 2, 1])
        f_squared_calc = np.array([10.0, 20.0, 30.0, 40.0])
        f_calc = np.array([3.0, 4.0, 5.0, 6.0])

    class Experiment:
        refln = Refln()

    tick_sets = Plotter()._extract_bragg_tick_sets(
        experiment=Experiment(),
        expt_name='E1',
        x_axis=XAxisType.TWO_THETA,
        x_min=1.0,
        x_max=3.0,
    )

    assert [tick_set.phase_id for tick_set in tick_sets] == ['phase-a', 'phase-b']
    assert np.allclose(tick_sets[0].x, np.array([1.5]))
    assert np.array_equal(tick_sets[0].h, np.array([2]))
    assert np.array_equal(tick_sets[1].h, np.array([3]))
    assert np.array_equal(tick_sets[1].k, np.array([1]))
    assert np.array_equal(tick_sets[1].ell, np.array([2]))
    assert np.allclose(tick_sets[0].f_squared_calc, np.array([20.0]))
    assert np.allclose(tick_sets[1].f_calc, np.array([5.0]))


def test_extract_bragg_tick_sets_returns_empty_without_category():
    from easydiffraction.display.plotting import Plotter
    from easydiffraction.display.plotting import XAxisType

    class Experiment:
        pass

    tick_sets = Plotter()._extract_bragg_tick_sets(
        experiment=Experiment(),
        expt_name='E1',
        x_axis=XAxisType.TWO_THETA,
        x_min=1.0,
        x_max=3.0,
    )

    assert tick_sets == ()


def _make_bayesian_plotter_fixture():
    from easydiffraction.analysis.fit_helpers.bayesian import PosteriorParameterSummary
    from easydiffraction.analysis.fit_helpers.bayesian import PosteriorSamples
    from easydiffraction.display.plotting import Plotter

    samples = np.array(
        [
            [[3.8900, 0.0760, -0.1170, 0.6290], [3.8908, 0.0775, -0.1185, 0.6300]],
            [[3.8912, 0.0785, -0.1190, 0.6310], [3.8916, 0.0790, -0.1200, 0.6320]],
        ],
        dtype=float,
    )
    parameter_names = ['length_a', 'broad_gauss_u', 'broad_gauss_v', 'twotheta_offset']
    posterior_samples = PosteriorSamples(
        parameter_names=parameter_names,
        parameter_samples=samples,
        log_posterior=np.array([[0.1, 0.2], [0.3, 0.4]], dtype=float),
    )
    parameters = [
        SimpleNamespace(unique_name='length_a', name='length_a', fit_min=3.8895, fit_max=3.8920),
        SimpleNamespace(
            unique_name='broad_gauss_u', name='broad_gauss_u', fit_min=0.05, fit_max=0.11
        ),
        SimpleNamespace(
            unique_name='broad_gauss_v', name='broad_gauss_v', fit_min=-0.14, fit_max=-0.10
        ),
        SimpleNamespace(
            unique_name='twotheta_offset', name='twotheta_offset', fit_min=0.625, fit_max=0.64
        ),
    ]
    summaries = [
        PosteriorParameterSummary(
            unique_name=name,
            display_name=name,
            best_sample_value=float(samples[-1, -1, index]),
            median=float(np.median(samples[:, :, index])),
            standard_deviation=float(np.std(samples[:, :, index], ddof=1)),
            interval_68=tuple(np.quantile(samples[:, :, index], [0.16, 0.84]).tolist()),
            interval_95=tuple(np.quantile(samples[:, :, index], [0.025, 0.975]).tolist()),
        )
        for index, name in enumerate(parameter_names)
    ]
    fit_results = SimpleNamespace(
        posterior_samples=posterior_samples,
        posterior_parameter_summaries=summaries,
        posterior_predictive={},
        parameters=parameters,
    )
    plotter = Plotter()
    plotter._get_posterior_samples_and_fit_results = MethodType(
        lambda self: (posterior_samples, fit_results),
        plotter,
    )
    plotter._get_fit_result_for_correlation = MethodType(lambda self: fit_results, plotter)
    return plotter, fit_results, posterior_samples


def test_correlation_from_posterior_samples_returns_labeled_dataframe():
    from easydiffraction.display.plotting import Plotter

    _, _, posterior_samples = _make_bayesian_plotter_fixture()

    corr_df = Plotter()._correlation_from_posterior_samples(posterior_samples)

    assert list(corr_df.index) == posterior_samples.parameter_names
    assert list(corr_df.columns) == posterior_samples.parameter_names
    np.testing.assert_allclose(np.diag(corr_df.to_numpy()), np.ones(len(corr_df)))


def test_build_posterior_pairs_plot_hides_diagonal_ticks_and_uses_annotations():
    from easydiffraction.display.plotting import POSTERIOR_PAIR_SAMPLE_MARKER_SIZE
    from easydiffraction.display.plotting import POSTERIOR_PAIR_TITLE_FONT_SIZE
    from easydiffraction.display.plotting import SQUARE_MATRIX_BOTTOM_MARGIN_PIXELS
    from easydiffraction.display.plotting import SQUARE_MATRIX_TITLE_YSHIFT_PIXELS
    from easydiffraction.display.plotting import SQUARE_MATRIX_TOP_MARGIN_PIXELS

    plotter, _, _ = _make_bayesian_plotter_fixture()

    figure = plotter._build_posterior_pairs_plot(parameters=None)

    assert figure.layout.title.text is None
    assert figure.layout.autosize is True
    assert figure.layout.width is None
    assert figure.layout.height is None
    assert (
        figure.layout.meta['fixed_aspect_wrapper']['aspect_ratio']
        == plotter._square_matrix_layout_meta(
            n_parameters=4,
            annotation_labels=[
                'length_a',
                'broad_gauss_u',
                'broad_gauss_v',
                'twotheta_offset',
            ],
        )['fixed_aspect_wrapper']['aspect_ratio']
    )
    theme_sync = figure.layout.meta['ed_plotly_theme_sync']
    assert theme_sync['axis_frame_shape_indexes'] == [
        index for index, shape in enumerate(figure.layout.shapes) if shape.type == 'rect'
    ]
    assert [annotation.text for annotation in figure.layout.annotations] == [
        'Posterior pair plot',
        'length_a',
        'broad_gauss_u',
        'broad_gauss_v',
        'twotheta_offset',
        'length_a',
        'broad_gauss_u',
        'broad_gauss_v',
        'twotheta_offset',
    ]
    assert figure.layout.annotations[0].font.size == POSTERIOR_PAIR_TITLE_FONT_SIZE
    assert figure.layout.annotations[0].yshift == SQUARE_MATRIX_TITLE_YSHIFT_PIXELS
    assert figure.layout.annotations[0].xshift == -plotter._square_matrix_title_left_shift([
        'length_a',
        'broad_gauss_u',
        'broad_gauss_v',
        'twotheta_offset',
    ])
    assert figure.layout.margin.t == SQUARE_MATRIX_TOP_MARGIN_PIXELS
    assert figure.layout.margin.b == SQUARE_MATRIX_BOTTOM_MARGIN_PIXELS
    subplot = figure.get_subplot(1, 1)
    bottom_subplot = figure.get_subplot(4, 1)
    assert subplot.yaxis.showticklabels is False
    assert subplot.yaxis.ticks == ''
    assert subplot.yaxis.ticklen == 0
    assert subplot.yaxis.title.text is None
    assert bottom_subplot.xaxis.showticklabels is False
    assert bottom_subplot.xaxis.title.text is None
    assert figure.layout.paper_bgcolor is None
    assert figure.layout.plot_bgcolor is None
    assert len(figure.layout.shapes) == 30
    assert any(trace.name == 'Posterior contours' for trace in figure.data)
    sample_trace = next(trace for trace in figure.data if trace.name == 'Posterior samples')
    assert sample_trace.marker.size == POSTERIOR_PAIR_SAMPLE_MARKER_SIZE
    # The visible scatter carries hover directly -- no duplicate transparent
    # layer embedding a second copy of every sample point.
    assert sample_trace.hovertemplate is not None
    assert not any(
        getattr(trace, 'mode', None) == 'markers'
        and getattr(trace.marker, 'color', None) == 'rgba(0, 0, 0, 0)'
        for trace in figure.data
    )


def test_build_posterior_pairs_plot_fast_mode_skips_contours():
    plotter, _, _ = _make_bayesian_plotter_fixture()

    figure = plotter._build_posterior_pairs_plot(parameters=None, style='fast')

    assert all(trace.name != 'Posterior contours' for trace in figure.data)


def test_build_posterior_pairs_plot_sign_colors_contours_and_marginals():
    from easydiffraction.display.plotting import POSTERIOR_CONTOUR_FILL_COLORSCALE
    from easydiffraction.display.plotting import POSTERIOR_CONTOUR_LINE_COLORSCALE
    from easydiffraction.display.plotting import POSTERIOR_NEGATIVE_CONTOUR_FILL_COLORSCALE
    from easydiffraction.display.plotting import POSTERIOR_NEGATIVE_CONTOUR_LINE_COLORSCALE
    from easydiffraction.display.plotting import POSTERIOR_PAIR_MARGINAL_DENSITY_FILL_COLOR
    from easydiffraction.display.plotting import POSTERIOR_PAIR_MARGINAL_DENSITY_LINE_COLOR
    from easydiffraction.display.plotting import POSTERIOR_PAIR_MARGINAL_DENSITY_LINE_WIDTH

    plotter, _, _ = _make_bayesian_plotter_fixture()

    figure = plotter._build_posterior_pairs_plot(parameters=None)

    marginal_traces = [trace for trace in figure.data if trace.name == 'Marginal density']
    assert marginal_traces
    assert all(
        trace.line.color == POSTERIOR_PAIR_MARGINAL_DENSITY_LINE_COLOR for trace in marginal_traces
    )
    assert all(
        trace.line.width == POSTERIOR_PAIR_MARGINAL_DENSITY_LINE_WIDTH for trace in marginal_traces
    )
    assert all(
        trace.fillcolor == POSTERIOR_PAIR_MARGINAL_DENSITY_FILL_COLOR for trace in marginal_traces
    )

    fill_contours = [
        trace
        for trace in figure.data
        if trace.type == 'contour' and trace.contours.coloring == 'fill'
    ]
    line_contours = [
        trace
        for trace in figure.data
        if trace.type == 'contour' and trace.contours.coloring == 'lines'
    ]
    fill_end_colors = {trace.colorscale[-1][1] for trace in fill_contours}
    line_end_colors = {trace.colorscale[-1][1] for trace in line_contours}

    assert POSTERIOR_CONTOUR_FILL_COLORSCALE[-1][1] in fill_end_colors
    assert POSTERIOR_NEGATIVE_CONTOUR_FILL_COLORSCALE[-1][1] in fill_end_colors
    assert POSTERIOR_CONTOUR_LINE_COLORSCALE[-1][1] in line_end_colors
    assert POSTERIOR_NEGATIVE_CONTOUR_LINE_COLORSCALE[-1][1] in line_end_colors


def test_build_posterior_pairs_plot_formats_dotted_axis_titles_multiline():
    from easydiffraction.display.plotting import SQUARE_MATRIX_BOTTOM_MARGIN_PIXELS
    from easydiffraction.display.plotting import SQUARE_MATRIX_LEFT_MARGIN_PIXELS

    plotter, fit_results, _ = _make_bayesian_plotter_fixture()
    dotted_parameter_names = [
        'lbco.cell.length_a',
        'hrpt.peak.broad_gauss_u',
        'hrpt.peak.broad_gauss_v',
        'hrpt.instrument.twotheta_offset',
    ]
    fit_results.posterior_samples.parameter_names = dotted_parameter_names
    for index, unique_name in enumerate(dotted_parameter_names):
        fit_results.parameters[index].unique_name = unique_name
        fit_results.posterior_parameter_summaries[index].unique_name = unique_name

    figure = plotter._build_posterior_pairs_plot(parameters=None)

    annotation_texts = [annotation.text for annotation in figure.layout.annotations]
    assert 'hrpt.<br>peak.<br>broad_gauss_u' in annotation_texts
    assert 'hrpt.<br>instrument.<br>twotheta_offset' in annotation_texts
    assert all('None broad_gauss_u' not in text for text in annotation_texts)
    assert figure.layout.margin.l > SQUARE_MATRIX_LEFT_MARGIN_PIXELS
    assert figure.layout.margin.b > SQUARE_MATRIX_BOTTOM_MARGIN_PIXELS


def test_build_posterior_pairs_plot_uses_full_names_in_hovertemplates():
    plotter, fit_results, _ = _make_bayesian_plotter_fixture()
    dotted_parameter_names = [
        'lbco.cell.length_a',
        'hrpt.peak.broad_gauss_u',
        'hrpt.peak.broad_gauss_v',
        'hrpt.instrument.twotheta_offset',
    ]
    fit_results.posterior_samples.parameter_names = dotted_parameter_names
    for index, unique_name in enumerate(dotted_parameter_names):
        fit_results.parameters[index].unique_name = unique_name
        fit_results.posterior_parameter_summaries[index].unique_name = unique_name

    figure = plotter._build_posterior_pairs_plot(parameters=None)

    hovertemplates = {
        trace.hovertemplate
        for trace in figure.data
        if getattr(trace, 'hovertemplate', None) is not None
    }

    assert (
        'lbco.cell.length_a: %{x:.4f}<br>hrpt.peak.broad_gauss_u: %{y:.4f}<extra></extra>'
    ) in hovertemplates
    assert (
        'hrpt.instrument.twotheta_offset: %{x:.4f}<br>density: %{y:.4f}<extra></extra>'
    ) in hovertemplates


def test_posterior_pair_figure_height_shrinks_cells_for_many_parameters():
    from easydiffraction.display.plotting import PAIR_PLOT_CELL_SIZE_PIXELS
    from easydiffraction.display.plotting import Plotter

    cell_size = Plotter._posterior_pair_cell_size_pixels(8, available_width_pixels=980)

    assert cell_size < PAIR_PLOT_CELL_SIZE_PIXELS


def test_posterior_pair_density_budget_scales_with_parameter_count():
    from easydiffraction.display.plotting import Plotter

    assert Plotter._posterior_pair_density_max_points(
        8
    ) < Plotter._posterior_pair_density_max_points(4)
    assert Plotter._posterior_pair_contour_grid_size(
        8
    ) < Plotter._posterior_pair_contour_grid_size(4)


def test_posterior_pairs_context_thins_kde_samples_and_preserves_axis_ranges():
    from easydiffraction.analysis.fit_helpers.bayesian import PosteriorSamples
    from easydiffraction.display.plotting import POSTERIOR_PAIR_SCATTER_MAX_POINTS
    from easydiffraction.display.plotting import Plotter

    parameter_count = 8
    sample_count = 5000
    parameter_names = [f'param_{index}' for index in range(parameter_count)]
    samples = np.zeros((1, sample_count, parameter_count), dtype=float)
    samples[0, 1, 0] = 100.0
    samples[0, 2, 1] = -50.0
    for index in range(2, parameter_count):
        samples[0, :, index] = np.linspace(index, index + 1, sample_count, dtype=float)

    posterior_samples = PosteriorSamples(
        parameter_names=parameter_names,
        parameter_samples=samples,
        log_posterior=np.zeros((1, sample_count), dtype=float),
    )
    parameters = [
        SimpleNamespace(unique_name=name, name=name, fit_min=None, fit_max=None)
        for name in parameter_names
    ]
    fit_results = SimpleNamespace(
        posterior_samples=posterior_samples,
        posterior_parameter_summaries=[],
        posterior_predictive={},
        parameters=parameters,
    )
    plotter = Plotter()
    plotter._get_posterior_samples_and_fit_results = MethodType(
        lambda self: (posterior_samples, fit_results),
        plotter,
    )

    context = plotter._posterior_pairs_context(parameters=None)

    assert context is not None
    assert context.marginal_density_samples.shape == (sample_count, parameter_count)
    assert context.density_samples.shape == (
        Plotter._posterior_pair_density_max_points(parameter_count),
        parameter_count,
    )
    assert context.scatter_samples.shape == (POSTERIOR_PAIR_SCATTER_MAX_POINTS, parameter_count)
    assert context.show_contours is False
    assert context.contour_grid_size == Plotter._posterior_pair_contour_grid_size(parameter_count)
    assert context.axis_ranges[0][1] > 100.0
    assert context.axis_ranges[1][0] < -50.0


def test_posterior_pair_diagonal_matches_standalone_distribution_when_thinned():
    from easydiffraction.analysis.fit_helpers.bayesian import PosteriorParameterSummary
    from easydiffraction.analysis.fit_helpers.bayesian import PosteriorSamples
    from easydiffraction.display.plotting import Plotter

    sample_count = 5001
    angle = np.linspace(0.0, 12.0 * np.pi, sample_count, dtype=float)
    sample_axis = np.linspace(-1.0, 1.0, sample_count, dtype=float)
    samples = np.empty((1, sample_count, 2), dtype=float)
    samples[0, :, 0] = 3.8913 + 0.00016 * np.sin(angle) + 0.00003 * np.cos(2.0 * angle)
    samples[0, :, 1] = 0.0780 + 0.0024 * np.cos(0.5 * angle) + 0.0005 * sample_axis**2
    parameter_names = ['length_a', 'broad_gauss_u']
    posterior_samples = PosteriorSamples(
        parameter_names=parameter_names,
        parameter_samples=samples,
        log_posterior=np.zeros((1, sample_count), dtype=float),
    )
    parameters = [
        SimpleNamespace(unique_name='length_a', name='length_a', fit_min=3.8909, fit_max=3.8917),
        SimpleNamespace(
            unique_name='broad_gauss_u',
            name='broad_gauss_u',
            fit_min=0.074,
            fit_max=0.082,
        ),
    ]
    summaries = [
        PosteriorParameterSummary(
            unique_name=name,
            display_name=name,
            best_sample_value=float(samples[0, -1, index]),
            median=float(np.median(samples[:, :, index])),
            standard_deviation=float(np.std(samples[:, :, index], ddof=1)),
            interval_68=tuple(np.quantile(samples[:, :, index], [0.16, 0.84]).tolist()),
            interval_95=tuple(np.quantile(samples[:, :, index], [0.025, 0.975]).tolist()),
        )
        for index, name in enumerate(parameter_names)
    ]
    fit_results = SimpleNamespace(
        posterior_samples=posterior_samples,
        posterior_parameter_summaries=summaries,
        posterior_predictive={},
        parameters=parameters,
    )
    plotter = Plotter()
    plotter._get_posterior_samples_and_fit_results = MethodType(
        lambda self: (posterior_samples, fit_results),
        plotter,
    )
    plotter._get_fit_result_for_correlation = MethodType(lambda self: fit_results, plotter)

    pair_figure = plotter._build_posterior_pairs_plot(parameters=parameters)
    distribution_figure = plotter._build_param_distribution_plot(parameters[0])

    pair_trace = next(
        trace
        for trace in pair_figure.data
        if trace.name == 'Marginal density'
        and trace.hovertemplate == 'length_a: %{x:.4f}<br>density: %{y:.4f}<extra></extra>'
    )
    distribution_trace = next(
        trace for trace in distribution_figure.data if trace.name == 'Marginal density'
    )

    np.testing.assert_allclose(pair_trace.x, distribution_trace.x)
    np.testing.assert_allclose(pair_trace.y, distribution_trace.y)


def test_build_posterior_pairs_plot_rejects_unknown_style():
    plotter, _, _ = _make_bayesian_plotter_fixture()

    with pytest.raises(
        ValueError,
        match=r'style must be one of auto, fast, full for posterior pair plots\.',
    ):
        plotter._build_posterior_pairs_plot(parameters=None, style='slow')


def test_build_param_distribution_plot_returns_plotly_figure():
    from easydiffraction.display.plotting import POSTERIOR_INTERVAL_95_FILL_COLOR
    from easydiffraction.display.plotting import POSTERIOR_PAIR_MARGINAL_DENSITY_FILL_COLOR
    from easydiffraction.display.plotting import POSTERIOR_PAIR_MARGINAL_DENSITY_LINE_COLOR
    from easydiffraction.display.plotting import POSTERIOR_PAIR_MARGINAL_DENSITY_LINE_WIDTH
    from easydiffraction.display.plotting import POSTERIOR_POINT_ESTIMATE_LINE_DASH

    plotter, fit_results, _ = _make_bayesian_plotter_fixture()
    parameter = fit_results.parameters[0]

    figure = plotter._build_param_distribution_plot(parameter)

    assert figure.layout.title.text == 'Posterior distribution: length_a'
    assert {trace.name for trace in figure.data} >= {
        'Posterior histogram',
        'Marginal density',
        '95% credible interval',
        'Median',
        'Best posterior sample',
    }
    marginal_trace = next(trace for trace in figure.data if trace.name == 'Marginal density')
    histogram_trace = next(trace for trace in figure.data if trace.name == 'Posterior histogram')
    interval_trace = next(trace for trace in figure.data if trace.name == '95% credible interval')
    max_posterior_trace = next(
        trace for trace in figure.data if trace.name == 'Best posterior sample'
    )
    assert marginal_trace.line.color == POSTERIOR_PAIR_MARGINAL_DENSITY_LINE_COLOR
    assert marginal_trace.line.width == POSTERIOR_PAIR_MARGINAL_DENSITY_LINE_WIDTH
    assert marginal_trace.fillcolor == POSTERIOR_PAIR_MARGINAL_DENSITY_FILL_COLOR
    assert marginal_trace.hovertemplate == 'length_a: %{x:.4f}<br>density: %{y:.4f}<extra></extra>'
    # The histogram is pre-binned server-side into a Bar trace (per-bin
    # densities only) so the raw posterior samples never enter the payload.
    assert histogram_trace.type == 'bar'
    assert histogram_trace.width is not None
    assert len(histogram_trace.x) == len(histogram_trace.y)
    assert '68% credible interval' not in {trace.name for trace in figure.data}
    assert interval_trace.fillcolor == POSTERIOR_INTERVAL_95_FILL_COLOR
    assert max_posterior_trace.line.dash == POSTERIOR_POINT_ESTIMATE_LINE_DASH
    assert figure.layout.xaxis.range is not None
    assert tuple(figure.layout.xaxis.range) == (
        float(marginal_trace.x[0]),
        float(marginal_trace.x[-1]),
    )
    assert figure.layout.yaxis.range is not None


def test_param_distribution_histogram_is_prebinned_not_raw_samples():
    """Distribution histogram embeds per-bin densities, not raw draws.

    A ``go.Histogram`` fed the full posterior sample array serialises
    every draw into the figure (megabytes for real chains), which left
    the lazy-figure "Loading plot…" skeleton unable to paint until the
    browser parsed the whole payload. The trace must instead carry only
    the pre-computed per-bin densities.
    """
    from easydiffraction.analysis.fit_helpers.bayesian import PosteriorParameterSummary
    from easydiffraction.analysis.fit_helpers.bayesian import PosteriorSamples
    from easydiffraction.display.plotting import Plotter

    rng = np.random.default_rng(0)
    sample_count = 5000
    draws = rng.normal(3.89, 0.001, size=(1, sample_count, 1))
    posterior_samples = PosteriorSamples(
        parameter_names=['length_a'],
        parameter_samples=draws,
        log_posterior=np.zeros((1, sample_count), dtype=float),
    )
    parameter = SimpleNamespace(
        unique_name='length_a', name='length_a', fit_min=3.885, fit_max=3.895
    )
    summary = PosteriorParameterSummary(
        unique_name='length_a',
        display_name='length_a',
        best_sample_value=float(draws[0, -1, 0]),
        median=float(np.median(draws)),
        standard_deviation=float(np.std(draws, ddof=1)),
        interval_68=tuple(np.quantile(draws, [0.16, 0.84]).tolist()),
        interval_95=tuple(np.quantile(draws, [0.025, 0.975]).tolist()),
    )
    fit_results = SimpleNamespace(
        posterior_samples=posterior_samples,
        posterior_parameter_summaries=[summary],
        posterior_predictive={},
        parameters=[parameter],
    )
    plotter = Plotter()
    plotter._get_posterior_samples_and_fit_results = MethodType(
        lambda self: (posterior_samples, fit_results), plotter
    )
    plotter._get_fit_result_for_correlation = MethodType(lambda self: fit_results, plotter)

    figure = plotter._build_param_distribution_plot(parameter)
    histogram_trace = next(t for t in figure.data if t.name == 'Posterior histogram')

    assert histogram_trace.type == 'bar'
    # Only per-bin densities ride along, far fewer than the raw draws.
    assert len(histogram_trace.y) < sample_count // 10
    assert len(histogram_trace.x) == len(histogram_trace.y)
    # Density-normalised bars integrate to ~1 across their bin widths.
    integral = float(np.sum(np.asarray(histogram_trace.y) * np.asarray(histogram_trace.width)))
    assert integral == pytest.approx(1.0, abs=1e-3)


def test_plot_param_distribution_routes_ascii_to_marginal_density(monkeypatch):
    from types import SimpleNamespace

    plotter, fit_results, posterior_samples = _make_bayesian_plotter_fixture()
    captured: dict[str, object] = {}
    plotter.engine = 'asciichartpy'
    plotter._backend = SimpleNamespace(
        plot_powder=lambda **kwargs: captured.setdefault('powder', kwargs)
    )

    plotter.plot_param_distribution(fit_results.parameters[0])

    values = posterior_samples.flattened()[:, 0]
    density_curve = plotter._posterior_density_curve(
        values,
        lower_bound=fit_results.parameters[0].fit_min,
        upper_bound=fit_results.parameters[0].fit_max,
    )

    assert density_curve is not None
    assert captured['powder']['labels'] == ['density']
    assert captured['powder']['axes_labels'] == ['length_a', 'Probability density']
    assert captured['powder']['title'] == 'Posterior distribution: length_a'
    assert captured['powder']['height'] == plotter.height
    np.testing.assert_allclose(captured['powder']['x'], density_curve[0])
    np.testing.assert_allclose(captured['powder']['y_series'][0], density_curve[1])


def test_plot_posterior_predictive_summary_uses_consistent_labels_and_styles(monkeypatch):
    from types import SimpleNamespace

    from easydiffraction.display.plotters.plotly import PlotlyPlotter
    from easydiffraction.display.plotting import POSTERIOR_INTERVAL_95_FILL_COLOR
    from easydiffraction.display.plotting import POSTERIOR_POINT_ESTIMATE_LINE_DASH
    from easydiffraction.display.plotting import Plotter

    captured: dict[str, object] = {}

    plotter = Plotter()
    plotter.engine = 'plotly'
    plotter._backend = SimpleNamespace(
        _show_figure=lambda figure: captured.setdefault('fig', figure)
    )

    plotter._plot_posterior_predictive_summary(
        expt_name='hrpt',
        summary=SimpleNamespace(
            x=np.array([1.0, 2.0, 3.0]),
            lower_95=np.array([8.0, 9.0, 10.0]),
            upper_95=np.array([10.0, 11.0, 12.0]),
            best_sample_prediction=np.array([9.0, 10.0, 11.0]),
        ),
        y_meas=np.array([9.5, 10.5, 11.5]),
        axes_labels=['2θ (deg)', 'Intensity (arb. units)'],
        show_band=True,
        show_draws=False,
    )

    fig = captured['fig']
    upper_band_trace = fig.data[1]
    measured_trace = next(trace for trace in fig.data if trace.name == 'Measured')
    max_posterior_trace = next(
        trace for trace in fig.data if trace.name == 'Best posterior sample'
    )

    assert upper_band_trace.name == '95% credible interval'
    assert upper_band_trace.fillcolor == POSTERIOR_INTERVAL_95_FILL_COLOR
    assert upper_band_trace.legendrank == 30
    assert measured_trace.legendrank == 10
    assert max_posterior_trace.legendrank == 20
    assert max_posterior_trace.line.dash == POSTERIOR_POINT_ESTIMATE_LINE_DASH
    assert fig.layout.legend.x == 0.99
    assert fig.layout.legend.y == 0.99
    assert fig.layout.legend.bgcolor == PlotlyPlotter._legend_background_color()
    assert fig.layout.margin.r == 30
    assert fig.layout.margin.t == 40
    assert fig.layout.margin.b == 45
    assert fig.layout.xaxis.showline is True
    assert fig.layout.xaxis.mirror is True
    assert fig.layout.xaxis.zeroline is False
    assert fig.layout.xaxis.linecolor == PlotlyPlotter._axis_frame_color()
    assert fig.layout.yaxis.showline is True
    assert fig.layout.yaxis.mirror is True
    assert fig.layout.yaxis.zeroline is False
    assert fig.layout.yaxis.linecolor == PlotlyPlotter._axis_frame_color()


@pytest.mark.parametrize(
    ('x_values', 'y_values', 'x_bounds', 'y_bounds'),
    [
        (np.ones(8), np.arange(8, dtype=float), (0.5, 1.5), (0.0, 7.0)),
        (
            np.arange(8, dtype=float),
            2.0 * np.arange(8, dtype=float) + 1.0,
            (0.0, 7.0),
            (1.0, 15.0),
        ),
    ],
)
def test_posterior_pair_density_surface_returns_none_for_rank_deficient_samples(
    x_values,
    y_values,
    x_bounds,
    y_bounds,
):
    from easydiffraction.display.plotting import Plotter

    surface = Plotter._posterior_pair_density_surface(
        x_values=np.asarray(x_values, dtype=float),
        y_values=np.asarray(y_values, dtype=float),
        x_bounds=x_bounds,
        y_bounds=y_bounds,
    )

    assert surface is None


def test_plot_posterior_predictive_data_uses_max_posterior_label_and_dash(monkeypatch):
    from types import SimpleNamespace

    from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
    from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
    from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum
    from easydiffraction.display.plotting import Plotter
    from easydiffraction.display.plotting import XAxisType

    captured: dict[str, object] = {}

    class ExptType:
        sample_form = type('SF', (), {'value': SampleFormEnum.POWDER})()
        scattering_type = type('S', (), {'value': ScatteringTypeEnum.BRAGG})()
        beam_mode = type('B', (), {'value': BeamModeEnum.CONSTANT_WAVELENGTH})()

    class Pattern:
        two_theta = np.array([1.0, 2.0, 3.0])
        intensity_meas = np.array([10.0, 12.0, 11.0])
        intensity_bkg = np.array([1.0, 1.0, 1.0])

    class Experiment:
        type = ExptType()
        data = Pattern()

    plotter = Plotter()
    plotter.engine = 'plotly'
    plotter._backend = SimpleNamespace(
        plot_powder_meas_vs_calc=lambda *, plot_spec: captured.setdefault('plot_spec', plot_spec)
    )

    monkeypatch.setattr(
        Plotter,
        '_get_or_build_posterior_predictive_summary',
        lambda self, **kwargs: SimpleNamespace(
            x=np.array([1.0, 2.0, 3.0]),
            lower_95=np.array([8.0, 9.0, 10.0]),
            upper_95=np.array([10.0, 11.0, 12.0]),
            best_sample_prediction=np.array([9.0, 11.0, 10.5]),
            draws=None,
        ),
    )
    monkeypatch.setattr(Plotter, '_extract_bragg_tick_sets', lambda self, **kwargs: ())

    plotter._plot_posterior_predictive_data(
        experiment=Experiment(),
        expt_name='hrpt',
        plot_options=SimpleNamespace(
            x_min=None,
            x_max=None,
            show_residual=None,
            show_background=None,
            show_bragg=None,
            show_excluded=False,
            x=None,
        ),
        x_axis=XAxisType.TWO_THETA,
        style='band',
    )

    plot_spec = captured['plot_spec']
    assert plot_spec.y_calc_name == 'Best posterior sample'
    assert plot_spec.y_calc_line_dash == 'dot'


def test_plot_posterior_predictive_request_allows_ascii_for_powder_bragg(monkeypatch):
    from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
    from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
    from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum
    from easydiffraction.display.plotting import Plotter

    captured: dict[str, object] = {}

    class ExptType:
        sample_form = type('SF', (), {'value': SampleFormEnum.POWDER})()
        scattering_type = type('S', (), {'value': ScatteringTypeEnum.BRAGG})()
        beam_mode = type('B', (), {'value': BeamModeEnum.CONSTANT_WAVELENGTH})()

    class Experiment:
        type = ExptType()

    class Project:
        experiments = {'hrpt': Experiment()}

    plotter = Plotter()
    plotter.engine = 'asciichartpy'
    plotter._set_project(Project())

    monkeypatch.setattr(Plotter, '_update_project_categories', lambda self, expt_name: None)

    def fake_plot_posterior_predictive_data(
        self,
        *,
        experiment,
        expt_name,
        plot_options,
        x_axis,
        style,
    ):
        captured['experiment'] = experiment
        captured['expt_name'] = expt_name
        captured['style'] = style
        captured['x_axis'] = x_axis
        captured['show_residual'] = plot_options.show_residual

    monkeypatch.setattr(
        Plotter, '_plot_posterior_predictive_data', fake_plot_posterior_predictive_data
    )

    plotter.plot_posterior_predictive('hrpt')

    assert captured['experiment'] is Project.experiments['hrpt']
    assert captured['expt_name'] == 'hrpt'
    assert captured['style'] == 'band'
    assert captured['show_residual'] is None


def test_plot_posterior_predictive_summary_routes_ascii_to_measured_and_map(monkeypatch):
    from types import SimpleNamespace

    from easydiffraction.display.plotting import Plotter

    captured: dict[str, object] = {}
    plotter = Plotter()
    plotter.engine = 'asciichartpy'
    plotter._backend = SimpleNamespace(
        plot_powder=lambda **kwargs: captured.setdefault('powder', kwargs)
    )

    plotter._plot_posterior_predictive_summary(
        expt_name='pdf',
        summary=SimpleNamespace(
            x=np.array([1.0, 2.0, 3.0]),
            best_sample_prediction=np.array([9.0, 10.0, 11.0]),
            lower_95=np.array([8.0, 9.0, 10.0]),
            upper_95=np.array([10.0, 11.0, 12.0]),
            draws=np.array([[8.5, 9.5, 10.5]]),
        ),
        y_meas=np.array([9.5, 10.5, 11.5]),
        axes_labels=['2θ (deg)', 'Intensity (arb. units)'],
        show_band=True,
        show_draws=True,
        excluded_ranges=((1.2, 1.4),),
    )

    assert captured['powder']['labels'] == ['meas', 'posterior']
    np.testing.assert_allclose(captured['powder']['x'], np.array([1.0, 2.0, 3.0]))
    np.testing.assert_allclose(
        captured['powder']['y_series'][0],
        np.array([9.5, 10.5, 11.5]),
    )
    np.testing.assert_allclose(
        captured['powder']['y_series'][1],
        np.array([9.0, 10.0, 11.0]),
    )
    assert captured['powder']['excluded_ranges'] == ((1.2, 1.4),)


def test_plot_posterior_predictive_data_routes_ascii_to_line_plot_without_intervals(monkeypatch):
    from types import SimpleNamespace

    from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
    from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
    from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum
    from easydiffraction.display.plotting import Plotter
    from easydiffraction.display.plotting import XAxisType

    captured: dict[str, object] = {}

    class ExptType:
        sample_form = type('SF', (), {'value': SampleFormEnum.POWDER})()
        scattering_type = type('S', (), {'value': ScatteringTypeEnum.BRAGG})()
        beam_mode = type('B', (), {'value': BeamModeEnum.CONSTANT_WAVELENGTH})()

    class Pattern:
        two_theta = np.array([1.0, 2.0, 3.0])
        intensity_meas = np.array([10.0, 12.0, 11.0])
        intensity_bkg = np.array([1.0, 1.0, 1.0])

    class Experiment:
        type = ExptType()
        data = Pattern()

    plotter = Plotter()
    plotter.engine = 'asciichartpy'
    plotter._backend = SimpleNamespace(
        plot_powder=lambda **kwargs: captured.setdefault('powder', kwargs),
        plot_powder_meas_vs_calc=lambda **kwargs: captured.setdefault('composite', kwargs),
    )

    monkeypatch.setattr(
        Plotter,
        '_get_or_build_posterior_predictive_summary',
        lambda self, **kwargs: SimpleNamespace(
            x=np.array([1.0, 2.0, 3.0]),
            lower_95=np.array([8.0, 9.0, 10.0]),
            upper_95=np.array([10.0, 11.0, 12.0]),
            best_sample_prediction=np.array([9.0, 11.0, 10.5]),
            draws=None,
        ),
    )

    plotter._plot_posterior_predictive_data(
        experiment=Experiment(),
        expt_name='hrpt',
        plot_options=SimpleNamespace(
            x_min=None,
            x_max=None,
            show_residual=None,
            show_background=None,
            show_bragg=None,
            show_excluded=False,
            x=None,
        ),
        x_axis=XAxisType.TWO_THETA,
        style='band+draws',
    )

    assert 'composite' not in captured
    assert captured['powder']['labels'] == ['meas', 'posterior']
    np.testing.assert_allclose(captured['powder']['x'], np.array([1.0, 2.0, 3.0]))
    np.testing.assert_allclose(
        captured['powder']['y_series'][0],
        np.array([10.0, 12.0, 11.0]),
    )
    np.testing.assert_allclose(
        captured['powder']['y_series'][1],
        np.array([9.0, 11.0, 10.5]),
    )


def test_plot_meas_vs_calc_request_respects_background_and_bragg_flags():
    from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
    from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
    from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum
    from easydiffraction.display.plotting import Plotter
    from easydiffraction.display.plotting import _MeasVsCalcPlotOptions

    captured: dict[str, object] = {}

    class FakeBackend:
        def plot_powder_meas_vs_calc(self, *, plot_spec):
            captured['plot_spec'] = plot_spec

    class Pattern:
        two_theta = np.array([1.0, 2.0, 3.0])
        intensity_meas = np.array([10.0, 12.0, 11.0])
        intensity_calc = np.array([9.0, 11.0, 10.5])
        intensity_bkg = np.array([1.0, 1.0, 1.0])

    class Refln:
        phase_id = np.array(['phase-a'])
        two_theta = np.array([2.0])
        index_h = np.array([1])
        index_k = np.array([0])
        index_l = np.array([1])
        f_squared_calc = np.array([50.0])
        f_calc = np.array([7.0])

    class ExptType:
        sample_form = type('SF', (), {'value': SampleFormEnum.POWDER})()
        scattering_type = type('S', (), {'value': ScatteringTypeEnum.BRAGG})()
        beam_mode = type('B', (), {'value': BeamModeEnum.CONSTANT_WAVELENGTH})()

    class Experiment:
        data = Pattern()
        type = ExptType()
        refln = Refln()

    plotter = Plotter()
    plotter._backend = FakeBackend()
    plotter._plot_meas_vs_calc_data(
        experiment=Experiment(),
        expt_name='E1',
        plot_options=_MeasVsCalcPlotOptions(
            show_background=False,
            show_bragg=False,
        ),
    )

    plot_spec = captured['plot_spec']
    assert plot_spec.y_bkg is None
    assert plot_spec.bragg_tick_sets == ()

    plotter._plot_meas_vs_calc_data(
        experiment=Experiment(),
        expt_name='E1',
        plot_options=_MeasVsCalcPlotOptions(
            show_background=True,
            show_bragg=True,
        ),
    )

    plot_spec = captured['plot_spec']
    assert np.allclose(plot_spec.y_bkg, np.array([1.0, 1.0, 1.0]))
    assert len(plot_spec.bragg_tick_sets) == 1


def test_build_param_distribution_plot_accepts_unique_name_string():
    plotter, fit_results, posterior_samples = _make_bayesian_plotter_fixture()
    unique_name = 'phase.cell.length_a'
    posterior_samples.parameter_names[0] = unique_name
    fit_results.parameters[0].unique_name = unique_name
    fit_results.posterior_parameter_summaries[0].unique_name = unique_name

    figure = plotter._build_param_distribution_plot(unique_name)

    assert figure.layout.title.text == f'Posterior distribution: {unique_name}'


def test_build_param_distribution_plot_accepts_user_facing_label_string():
    plotter, fit_results, posterior_samples = _make_bayesian_plotter_fixture()
    unique_name = 'phase.cell.length_a'
    posterior_samples.parameter_names[0] = unique_name
    fit_results.parameters[0].unique_name = unique_name
    fit_results.posterior_parameter_summaries[0].unique_name = unique_name
    fit_results.posterior_parameter_summaries[0].display_name = 'Cell a'

    figure = plotter._build_param_distribution_plot('Cell a')

    assert figure.layout.title.text == f'Posterior distribution: {unique_name}'


def test_resolve_posterior_parameter_names_warns_on_ambiguous_label(monkeypatch):
    from easydiffraction.analysis.fit_helpers.bayesian import PosteriorParameterSummary
    from easydiffraction.analysis.fit_helpers.bayesian import PosteriorSamples
    from easydiffraction.display.plotting import Plotter

    posterior_samples = PosteriorSamples(
        parameter_names=['phase_a.length_a', 'phase_b.length_a'],
        parameter_samples=np.ones((2, 2, 2), dtype=float),
    )
    fit_results = SimpleNamespace(
        posterior_samples=posterior_samples,
        posterior_parameter_summaries=[
            PosteriorParameterSummary(
                unique_name='phase_a.length_a',
                display_name='length_a',
                best_sample_value=1.0,
                median=1.0,
                standard_deviation=0.1,
                interval_68=(0.9, 1.1),
                interval_95=(0.8, 1.2),
            ),
            PosteriorParameterSummary(
                unique_name='phase_b.length_a',
                display_name='length_a',
                best_sample_value=2.0,
                median=2.0,
                standard_deviation=0.1,
                interval_68=(1.9, 2.1),
                interval_95=(1.8, 2.2),
            ),
        ],
        parameters=[
            SimpleNamespace(unique_name='phase_a.length_a', name='length_a'),
            SimpleNamespace(unique_name='phase_b.length_a', name='length_a'),
        ],
    )
    warning_messages: list[str] = []

    monkeypatch.setattr(
        'easydiffraction.display.plotting.log.warning',
        warning_messages.append,
    )

    result = Plotter._resolve_posterior_parameter_names(
        fit_results=fit_results,
        parameters=['length_a'],
    )

    assert result is None
    assert warning_messages
    assert 'ambiguous' in warning_messages[0]
    assert 'phase_a.length_a' in warning_messages[0]
    assert 'phase_b.length_a' in warning_messages[0]


def test_build_posterior_predictive_summary_restores_parameter_state(monkeypatch):
    from easydiffraction.analysis.fit_helpers.bayesian import PosteriorPredictiveSummary
    from easydiffraction.display.plotting import Plotter

    class FakePredictiveParameter:
        def __init__(self, unique_name, value, uncertainty):
            self.unique_name = unique_name
            self.value = value
            self.uncertainty = uncertainty

        def _set_value_from_minimizer(self, value):
            self.value = value

    sampled_parameters = [
        FakePredictiveParameter('a', 1.0, 0.1),
        FakePredictiveParameter('b', 2.0, 0.2),
    ]
    posterior_samples = SimpleNamespace(
        parameter_names=['a', 'b'],
        flattened=lambda: np.array(
            [
                [1.0, 2.0],
                [1.1, 2.1],
                [0.9, 1.9],
                [1.2, 2.2],
            ],
            dtype=float,
        ),
    )
    fit_results = SimpleNamespace(
        posterior_samples=posterior_samples,
        parameters=sampled_parameters,
    )
    plotter = Plotter()

    def fake_evaluate(self, *, sampled_parameters, values, experiment, expt_name, x_axis):
        x = np.array([0.0, 1.0], dtype=float)
        y = np.array([values[0] + values[1], values[0] - values[1]], dtype=float)
        return y, x

    monkeypatch.setattr(Plotter, '_evaluate_posterior_predictive_state', fake_evaluate)
    monkeypatch.setattr(Plotter, '_update_project_categories', lambda self, expt_name: None)

    summary = plotter._build_posterior_predictive_summary(
        fit_results=fit_results,
        experiment=object(),
        expt_name='hrpt',
        x_axis='two_theta',
    )

    assert isinstance(summary, PosteriorPredictiveSummary)
    assert summary.experiment_name == 'hrpt'
    assert summary.x_axis_name == 'two_theta'
    assert summary.draws.shape == (4, 2)
    np.testing.assert_allclose(summary.best_sample_prediction, np.array([3.0, -1.0]))
    np.testing.assert_allclose([parameter.value for parameter in sampled_parameters], [1.0, 2.0])
    assert [parameter.uncertainty for parameter in sampled_parameters] == [0.1, 0.2]


def test_build_posterior_predictive_summary_omits_draws_when_not_requested(monkeypatch):
    from easydiffraction.display.plotting import Plotter

    class FakePredictiveParameter:
        def __init__(self, unique_name, value, uncertainty):
            self.unique_name = unique_name
            self.value = value
            self.uncertainty = uncertainty

        def _set_value_from_minimizer(self, value):
            self.value = value

    sampled_parameters = [
        FakePredictiveParameter('a', 1.0, 0.1),
        FakePredictiveParameter('b', 2.0, 0.2),
    ]
    posterior_samples = SimpleNamespace(
        parameter_names=['a', 'b'],
        flattened=lambda: np.array(
            [
                [1.0, 2.0],
                [1.1, 2.1],
                [0.9, 1.9],
                [1.2, 2.2],
            ],
            dtype=float,
        ),
    )
    fit_results = SimpleNamespace(
        posterior_samples=posterior_samples,
        parameters=sampled_parameters,
    )
    plotter = Plotter()

    def fake_evaluate(self, *, sampled_parameters, values, experiment, expt_name, x_axis):
        x = np.array([0.0, 1.0], dtype=float)
        y = np.array([values[0] + values[1], values[0] - values[1]], dtype=float)
        return y, x

    monkeypatch.setattr(Plotter, '_evaluate_posterior_predictive_state', fake_evaluate)
    monkeypatch.setattr(Plotter, '_update_project_categories', lambda self, expt_name: None)

    summary = plotter._build_posterior_predictive_summary(
        fit_results=fit_results,
        experiment=object(),
        expt_name='hrpt',
        x_axis='two_theta',
        include_draws=False,
    )

    assert summary is not None
    assert summary.draws is None
    np.testing.assert_allclose(summary.lower_95.shape, (2,))
    np.testing.assert_allclose(summary.upper_95.shape, (2,))


def test_get_or_build_posterior_predictive_summary_rebuilds_draws_after_band_cache(
    monkeypatch,
):
    from easydiffraction.display.plotting import Plotter

    fit_results = SimpleNamespace(
        posterior_predictive={},
        posterior_samples=object(),
    )
    band_summary = SimpleNamespace(draws=None)
    draw_summary = SimpleNamespace(draws=np.ones((2, 2), dtype=float))
    build_calls: list[bool] = []
    plotter = Plotter()

    monkeypatch.setattr(Plotter, '_get_fit_result_for_correlation', lambda self: fit_results)

    def fake_build(
        self,
        *,
        fit_results,
        experiment,
        expt_name,
        x_axis,
        include_draws=True,
    ):
        del fit_results, experiment, expt_name, x_axis
        build_calls.append(include_draws)
        return draw_summary if include_draws else band_summary

    monkeypatch.setattr(Plotter, '_build_posterior_predictive_summary', fake_build)

    summary_band = plotter._get_or_build_posterior_predictive_summary(
        experiment=object(),
        expt_name='hrpt',
        x_axis='two_theta',
        include_draws=False,
    )
    summary_draws = plotter._get_or_build_posterior_predictive_summary(
        experiment=object(),
        expt_name='hrpt',
        x_axis='two_theta',
        include_draws=True,
    )

    assert summary_band is band_summary
    assert summary_draws is draw_summary
    assert build_calls == [False, True]


def test_plot_posterior_predictive_defaults_to_band_for_bragg(monkeypatch):
    from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
    from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
    from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum
    from easydiffraction.display.plotting import Plotter

    captured: dict[str, object] = {}

    class ExptType:
        sample_form = type('SF', (), {'value': SampleFormEnum.POWDER})()
        scattering_type = type('S', (), {'value': ScatteringTypeEnum.BRAGG})()
        beam_mode = type('B', (), {'value': BeamModeEnum.CONSTANT_WAVELENGTH})()

    class Experiment:
        type = ExptType()

    class Project:
        experiments = {'hrpt': Experiment()}

    plotter = Plotter()
    plotter.engine = 'plotly'
    plotter._set_project(Project())

    monkeypatch.setattr(Plotter, '_update_project_categories', lambda self, expt_name: None)

    def fake_plot_posterior_predictive_data(
        self,
        *,
        experiment,
        expt_name,
        plot_options,
        x_axis,
        style,
    ):
        captured['experiment'] = experiment
        captured['expt_name'] = expt_name
        captured['style'] = style
        captured['x_axis'] = x_axis
        captured['show_residual'] = plot_options.show_residual

    monkeypatch.setattr(
        Plotter, '_plot_posterior_predictive_data', fake_plot_posterior_predictive_data
    )

    plotter.plot_posterior_predictive('hrpt')

    assert captured['experiment'] is Project.experiments['hrpt']
    assert captured['expt_name'] == 'hrpt'
    assert captured['style'] == 'band'
    assert captured['show_residual'] is None


def test_plot_posterior_predictive_non_bragg_filters_x_range_and_warns_for_residual(
    monkeypatch,
):
    from easydiffraction.analysis.fit_helpers.bayesian import PosteriorPredictiveSummary
    from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
    from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
    from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum
    from easydiffraction.display.plotting import Plotter

    captured: dict[str, object] = {}
    warnings: list[str] = []

    class ExptType:
        sample_form = type('SF', (), {'value': SampleFormEnum.POWDER})()
        scattering_type = type('S', (), {'value': ScatteringTypeEnum.TOTAL})()
        beam_mode = type('B', (), {'value': BeamModeEnum.CONSTANT_WAVELENGTH})()

    class Pattern:
        x = np.array([1.0, 2.0, 3.0])
        two_theta = np.array([1.0, 2.0, 3.0])
        intensity_meas = np.array([10.0, 20.0, 30.0])

    class Experiment:
        type = ExptType()
        data = Pattern()

    class Project:
        experiments = {'pdf': Experiment()}

    plotter = Plotter()
    plotter.engine = 'plotly'
    plotter._set_project(Project())

    monkeypatch.setattr(Plotter, '_update_project_categories', lambda self, expt_name: None)
    monkeypatch.setattr(
        Plotter,
        '_get_or_build_posterior_predictive_summary',
        lambda self, **kwargs: PosteriorPredictiveSummary(
            experiment_name='pdf',
            x_axis_name='two_theta',
            x=np.array([1.0, 2.0, 3.0]),
            best_sample_prediction=np.array([9.0, 19.0, 29.0]),
            lower_95=np.array([8.0, 18.0, 28.0]),
            upper_95=np.array([10.0, 20.0, 30.0]),
        ),
    )
    monkeypatch.setattr('easydiffraction.display.plotting.log.warning', warnings.append)

    def fake_plot_summary(
        self,
        *,
        expt_name,
        summary,
        y_meas,
        axes_labels,
        show_band,
        show_draws,
        excluded_ranges,
    ):
        captured['expt_name'] = expt_name
        captured['summary'] = summary
        captured['y_meas'] = y_meas
        captured['axes_labels'] = axes_labels
        captured['show_band'] = show_band
        captured['show_draws'] = show_draws
        captured['excluded_ranges'] = excluded_ranges

    monkeypatch.setattr(Plotter, '_plot_posterior_predictive_summary', fake_plot_summary)

    plotter.plot_posterior_predictive('pdf', x_min=1.5, x_max=2.5, show_residual=True)

    assert captured['expt_name'] == 'pdf'
    np.testing.assert_allclose(captured['summary'].x, np.array([2.0]))
    np.testing.assert_allclose(
        captured['summary'].best_sample_prediction,
        np.array([19.0]),
    )
    np.testing.assert_allclose(captured['summary'].lower_95, np.array([18.0]))
    np.testing.assert_allclose(captured['summary'].upper_95, np.array([20.0]))
    np.testing.assert_allclose(captured['y_meas'], np.array([20.0]))
    assert captured['show_band'] is True
    assert captured['show_draws'] is False
    assert captured['excluded_ranges'] == ()
    assert any('ignoring show_residual=True' in warning for warning in warnings)


def test_extract_bragg_tick_sets_uses_derived_d_spacing_for_cwl_ticks():
    import numpy as np

    from easydiffraction.display.plotting import Plotter
    from easydiffraction.display.plotting import XAxisType
    from easydiffraction.utils.utils import twotheta_to_d

    class Refln:
        phase_id = np.array(['phase-a'])
        two_theta = np.array([20.0])
        d_spacing = np.array([999.0])
        index_h = np.array([1])
        index_k = np.array([0])
        index_l = np.array([1])
        f_squared_calc = np.array([10.0])
        f_calc = np.array([3.0])

    class Instrument:
        setup_wavelength = type('Wavelength', (), {'value': 1.0})()

    class Experiment:
        refln = Refln()
        instrument = Instrument()

    tick_sets = Plotter()._extract_bragg_tick_sets(
        experiment=Experiment(),
        expt_name='E1',
        x_axis=XAxisType.D_SPACING,
        x_min=0.1,
        x_max=10.0,
    )

    np.testing.assert_allclose(tick_sets[0].x, twotheta_to_d(np.array([20.0]), 1.0))


def test_plot_meas_vs_calc_routes_powder_bragg_to_composite_backend():
    import numpy as np

    from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
    from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
    from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum
    from easydiffraction.display.plotting import Plotter
    from easydiffraction.display.plotting import _MeasVsCalcPlotOptions

    captured = {}

    class FakeBackend:
        def plot_powder_meas_vs_calc(self, **kwargs):
            captured['powder_meas_vs_calc'] = kwargs['plot_spec']

        def plot_powder(self, **kwargs):
            captured['powder'] = kwargs

    class Pattern:
        two_theta = np.array([0.0, 1.0, 2.0, 3.0])
        d_spacing = two_theta
        intensity_meas = np.array([10.0, 20.0, 30.0, 40.0])
        intensity_meas_su = np.array([0.1, 0.2, 0.3, 0.4])
        intensity_bkg = np.array([1.0, 2.0, 3.0, 4.0])
        intensity_calc = np.array([9.0, 18.0, 27.0, 39.0])

    class Refln:
        phase_id = np.array(['phase-a', 'phase-a', 'phase-b'])
        two_theta = np.array([0.5, 1.5, 2.0])
        index_h = np.array([1, 2, 3])
        index_k = np.array([0, 1, 1])
        index_l = np.array([1, 0, 2])
        f_squared_calc = np.array([100.0, 80.0, 60.0])
        f_calc = np.array([10.0, 9.0, 8.0])

    class ExptType:
        sample_form = type('SF', (), {'value': SampleFormEnum.POWDER})()
        scattering_type = type('S', (), {'value': ScatteringTypeEnum.BRAGG})()
        beam_mode = type('B', (), {'value': BeamModeEnum.CONSTANT_WAVELENGTH})()

    class Experiment:
        data = Pattern()
        type = ExptType()
        refln = Refln()

    plotter = Plotter()
    plotter._backend = FakeBackend()
    plotter._plot_meas_vs_calc_data(
        experiment=Experiment(),
        expt_name='E1',
        plot_options=_MeasVsCalcPlotOptions(x_min=1.0, x_max=2.0),
    )

    assert 'powder_meas_vs_calc' in captured
    assert 'powder' not in captured
    call = captured['powder_meas_vs_calc']
    assert np.allclose(call.x, np.array([1.0, 2.0]))
    assert np.allclose(call.y_meas, np.array([20.0, 30.0]))
    assert np.allclose(call.y_meas_su, np.array([0.2, 0.3]))
    assert np.allclose(call.y_bkg, np.array([2.0, 3.0]))
    assert np.allclose(call.y_calc, np.array([18.0, 27.0]))
    assert np.allclose(call.y_resid, np.array([2.0, 3.0]))
    assert [tick_set.phase_id for tick_set in call.bragg_tick_sets] == [
        'phase-a',
        'phase-b',
    ]
    assert np.allclose(call.bragg_tick_sets[0].x, np.array([1.5]))
    assert np.allclose(call.bragg_tick_sets[1].x, np.array([2.0]))


def test_plot_meas_vs_calc_extracts_bragg_ticks_with_default_bounds():
    import numpy as np

    from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
    from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
    from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum
    from easydiffraction.display.plotting import Plotter
    from easydiffraction.display.plotting import _MeasVsCalcPlotOptions

    captured = {}

    class FakeBackend:
        def plot_powder_meas_vs_calc(self, **kwargs):
            captured['powder_meas_vs_calc'] = kwargs['plot_spec']

    class Pattern:
        time_of_flight = np.array([10.0, 11.0, 12.0])
        intensity_meas = np.array([100.0, 110.0, 105.0])
        intensity_calc = np.array([99.0, 108.0, 104.0])

    class Refln:
        phase_id = np.array(['phase-a'])
        time_of_flight = np.array([11.0])
        index_h = np.array([1])
        index_k = np.array([0])
        index_l = np.array([1])
        f_squared_calc = np.array([50.0])
        f_calc = np.array([7.0])

    class ExptType:
        sample_form = type('SF', (), {'value': SampleFormEnum.POWDER})()
        scattering_type = type('S', (), {'value': ScatteringTypeEnum.BRAGG})()
        beam_mode = type('B', (), {'value': BeamModeEnum.TIME_OF_FLIGHT})()

    class Experiment:
        data = Pattern()
        type = ExptType()
        refln = Refln()

    plotter = Plotter()
    plotter._backend = FakeBackend()
    plotter._plot_meas_vs_calc_data(
        experiment=Experiment(),
        expt_name='E1',
        plot_options=_MeasVsCalcPlotOptions(),
    )

    call = captured['powder_meas_vs_calc']
    assert np.allclose(call.x, np.array([10.0, 11.0, 12.0]))
    assert [tick_set.phase_id for tick_set in call.bragg_tick_sets] == ['phase-a']
    assert np.allclose(call.bragg_tick_sets[0].x, np.array([11.0]))


def test_plot_meas_vs_calc_groups_numeric_bragg_structure_ids():
    import numpy as np

    from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
    from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
    from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum
    from easydiffraction.display.plotting import Plotter
    from easydiffraction.display.plotting import _MeasVsCalcPlotOptions

    captured = {}

    class FakeBackend:
        def plot_powder_meas_vs_calc(self, **kwargs):
            captured['powder_meas_vs_calc'] = kwargs['plot_spec']

    class Pattern:
        time_of_flight = np.array([10.0, 11.0, 12.0])
        intensity_meas = np.array([100.0, 110.0, 105.0])
        intensity_calc = np.array([99.0, 108.0, 104.0])

    class Refln:
        phase_id = np.array([1, 1, 2])
        time_of_flight = np.array([10.0, 11.0, 12.0])
        index_h = np.array([1, 2, 3])
        index_k = np.array([0, 1, 1])
        index_l = np.array([1, 0, 2])
        f_squared_calc = np.array([50.0, 40.0, 30.0])
        f_calc = np.array([7.0, 6.0, 5.0])

    class ExptType:
        sample_form = type('SF', (), {'value': SampleFormEnum.POWDER})()
        scattering_type = type('S', (), {'value': ScatteringTypeEnum.BRAGG})()
        beam_mode = type('B', (), {'value': BeamModeEnum.TIME_OF_FLIGHT})()

    class Experiment:
        data = Pattern()
        type = ExptType()
        refln = Refln()

    plotter = Plotter()
    plotter._backend = FakeBackend()
    plotter._plot_meas_vs_calc_data(
        experiment=Experiment(),
        expt_name='E1',
        plot_options=_MeasVsCalcPlotOptions(),
    )

    call = captured['powder_meas_vs_calc']
    assert [tick_set.phase_id for tick_set in call.bragg_tick_sets] == ['1', '2']
    assert np.allclose(call.bragg_tick_sets[0].x, np.array([10.0, 11.0]))
    assert np.allclose(call.bragg_tick_sets[1].x, np.array([12.0]))


def test_plot_meas_vs_calc_skips_bragg_ticks_when_filtered_pattern_is_empty():
    import numpy as np

    from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
    from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
    from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum
    from easydiffraction.display.plotting import Plotter
    from easydiffraction.display.plotting import _MeasVsCalcPlotOptions

    captured = {}

    class FakeBackend:
        def plot_powder_meas_vs_calc(self, **kwargs):
            captured['powder_meas_vs_calc'] = kwargs['plot_spec']

    class Pattern:
        time_of_flight = np.array([10.0, 11.0, 12.0])
        intensity_meas = np.array([100.0, 110.0, 105.0])
        intensity_calc = np.array([99.0, 108.0, 104.0])

    class Refln:
        phase_id = np.array(['phase-a'])
        time_of_flight = np.array([8.0])
        index_h = np.array([1])
        index_k = np.array([0])
        index_l = np.array([1])
        f_squared_calc = np.array([50.0])
        f_calc = np.array([7.0])

    class ExptType:
        sample_form = type('SF', (), {'value': SampleFormEnum.POWDER})()
        scattering_type = type('S', (), {'value': ScatteringTypeEnum.BRAGG})()
        beam_mode = type('B', (), {'value': BeamModeEnum.TIME_OF_FLIGHT})()

    class Experiment:
        data = Pattern()
        type = ExptType()
        refln = Refln()

    plotter = Plotter()
    plotter._backend = FakeBackend()
    plotter._plot_meas_vs_calc_data(
        experiment=Experiment(),
        expt_name='E1',
        plot_options=_MeasVsCalcPlotOptions(x_min=7.0, x_max=9.0),
    )

    call = captured['powder_meas_vs_calc']
    assert call.x.size == 0
    assert call.bragg_tick_sets == ()


def test_plot_meas_vs_calc_does_not_accept_layout_fraction_overrides():
    from easydiffraction.display.plotting import Plotter

    plotter = Plotter()

    with pytest.raises(TypeError, match='residual_height_fraction'):
        plotter.plot_meas_vs_calc('E1', residual_height_fraction=0.20)

    with pytest.raises(TypeError, match='bragg_peaks_height_fraction'):
        plotter.plot_meas_vs_calc('E1', bragg_peaks_height_fraction=0.20)


def test_plot_meas_vs_calc_keeps_single_crystal_routing():
    import numpy as np

    from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
    from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
    from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum
    from easydiffraction.display.plotting import Plotter
    from easydiffraction.display.plotting import _MeasVsCalcPlotOptions

    captured = {}

    class FakeBackend:
        def plot_single_crystal(self, **kwargs):
            captured['single_crystal'] = kwargs

        def plot_powder_meas_vs_calc(self, **kwargs):
            captured['powder_meas_vs_calc'] = kwargs['plot_spec']

    class Pattern:
        intensity_calc = np.array([1.0, 2.0, 3.0])
        intensity_meas = np.array([1.1, 1.9, 3.2])
        intensity_meas_su = np.array([0.1, 0.1, 0.1])

    class ExptType:
        sample_form = type('SF', (), {'value': SampleFormEnum.SINGLE_CRYSTAL})()
        scattering_type = type('S', (), {'value': ScatteringTypeEnum.BRAGG})()
        beam_mode = type('B', (), {'value': BeamModeEnum.CONSTANT_WAVELENGTH})()

    class Experiment:
        data = Pattern()
        type = ExptType()

    plotter = Plotter()
    plotter._backend = FakeBackend()
    plotter._plot_meas_vs_calc_data(
        experiment=Experiment(),
        expt_name='E1',
        plot_options=_MeasVsCalcPlotOptions(),
    )

    assert 'single_crystal' in captured
    assert 'powder_meas_vs_calc' not in captured
    assert np.allclose(captured['single_crystal']['x_calc'], np.array([1.0, 2.0, 3.0]))
    assert np.allclose(captured['single_crystal']['y_meas'], np.array([1.1, 1.9, 3.2]))
    assert np.allclose(captured['single_crystal']['y_meas_su'], np.array([0.1, 0.1, 0.1]))


def test_plot_meas_vs_calc_keeps_default_residual_off_for_line_paths():
    import numpy as np

    from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
    from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
    from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum
    from easydiffraction.display.plotting import Plotter
    from easydiffraction.display.plotting import _MeasVsCalcPlotOptions

    captured = {}

    class FakeBackend:
        def plot_powder(self, **kwargs):
            captured['powder'] = kwargs

        def plot_single_crystal(self, **kwargs):
            captured['single_crystal'] = kwargs

        def plot_powder_meas_vs_calc(self, **kwargs):
            captured['powder_meas_vs_calc'] = kwargs['plot_spec']

    class Pattern:
        d_spacing = np.array([1.0, 2.0, 3.0])
        intensity_meas = np.array([5.0, 6.0, 7.0])
        intensity_calc = np.array([4.5, 6.1, 7.2])

    class ExptType:
        sample_form = type('SF', (), {'value': SampleFormEnum.SINGLE_CRYSTAL})()
        scattering_type = type('S', (), {'value': ScatteringTypeEnum.BRAGG})()
        beam_mode = type('B', (), {'value': BeamModeEnum.CONSTANT_WAVELENGTH})()

    class Experiment:
        data = Pattern()
        type = ExptType()

    plotter = Plotter()
    plotter._backend = FakeBackend()
    plotter._plot_meas_vs_calc_data(
        experiment=Experiment(),
        expt_name='E1',
        plot_options=_MeasVsCalcPlotOptions(x='d_spacing'),
    )

    assert 'powder' in captured
    assert 'single_crystal' not in captured
    assert 'powder_meas_vs_calc' not in captured
    assert captured['powder']['labels'] == ['meas', 'calc']


def test_plot_param_correlations_renders_ascii_table(monkeypatch):
    import numpy as np

    from easydiffraction.display.plotting import Plotter
    from easydiffraction.display.tables import TableRenderer

    captured = {}

    class FakeTabler:
        def render(self, df):
            captured['df'] = df

    monkeypatch.setattr(TableRenderer, 'get', staticmethod(FakeTabler))

    class Param:
        def __init__(self, uid, unique_name):
            self._minimizer_uid = uid
            self.unique_name = unique_name

    class RawResult:
        covar = np.array([[4.0, 1.0], [1.0, 9.0]])
        var_names = ['p1', 'p2']

    class FitResults:
        engine_result = RawResult()
        parameters = [
            Param('p1', 'phase.cell.length_a'),
            Param('p2', 'phase.cell.length_b'),
        ]

    class Analysis:
        fit_results = FitResults()

    class Project:
        analysis = Analysis()

    p = Plotter()
    p.engine = 'asciichartpy'
    p._set_project(Project())
    p.plot_param_correlations(threshold=0.1, precision=3, show_diagonal=False)

    df = captured['df']
    assert [column.strip() for column in df.columns.get_level_values(0)] == [
        'parameter',
        '1',
    ]
    assert list(df.columns.get_level_values(1)) == ['left', 'right']
    assert list(df.index) == [0, 1]
    assert df.iloc[0, 0] == 'phase.cell.length_a'
    assert df.iloc[0, 1] == ''
    assert df.iloc[1, 0] == 'phase.cell.length_b'
    assert _strip_markup(df.iloc[1, 1]).strip() == '0.167'


def test_plot_param_correlations_renders_plotly_heatmap(monkeypatch):
    import numpy as np

    import easydiffraction.display.plotters.plotly as plotly_mod
    from easydiffraction.display.plotting import POSTERIOR_PAIR_TITLE_FONT_SIZE
    from easydiffraction.display.plotting import SQUARE_MATRIX_AXIS_TITLE_LINE_HEIGHT_PIXELS
    from easydiffraction.display.plotting import SQUARE_MATRIX_BOTTOM_MARGIN_PIXELS
    from easydiffraction.display.plotting import SQUARE_MATRIX_TITLE_YSHIFT_PIXELS
    from easydiffraction.display.plotting import SQUARE_MATRIX_TOP_MARGIN_PIXELS
    from easydiffraction.display.plotting import Plotter

    captured = {}

    def fake_show_figure(self, fig):
        captured['fig'] = fig

    monkeypatch.setattr(plotly_mod.PlotlyPlotter, '_show_figure', fake_show_figure)

    class Param:
        def __init__(self, uid, unique_name):
            self._minimizer_uid = uid
            self.unique_name = unique_name

    class RawResult:
        covar = np.array([[1.0, -0.5], [-0.5, 1.0]])
        var_names = ['p1', 'p2']

    class FitResults:
        engine_result = RawResult()
        parameters = [
            Param('p1', 'phase.scale'),
            Param('p2', 'phase.cell.length_c'),
        ]

    class Analysis:
        fit_results = FitResults()

    class Project:
        analysis = Analysis()

    p = Plotter()
    p.engine = 'plotly'
    p._set_project(Project())
    p.plot_param_correlations()

    fig = captured['fig']
    heatmap = fig.data[0]
    text_trace = fig.data[1]
    gap_width = Plotter._square_matrix_gap_data_width(2)
    assert len(fig.data) == 2
    assert heatmap.type == 'heatmap'
    assert list(heatmap.x) == pytest.approx([0.0, 1.0, 1.0 + gap_width, 2.0 + gap_width])
    assert list(heatmap.y) == pytest.approx([0.0, 1.0, 1.0 + gap_width, 2.0 + gap_width])
    assert heatmap.showscale is False
    assert heatmap.hovertemplate == (
        '%{customdata[0]}<br>%{customdata[1]}<br>correlation: %{z:.2f}<extra></extra>'
    )
    assert list(heatmap.customdata[2][0]) == ['phase.scale', 'phase.cell.length_c']
    assert pytest.approx(np.nanmin(np.asarray(heatmap.z, dtype=float)), rel=1e-9) == -0.5
    assert text_trace.type == 'scatter'
    assert text_trace.mode == 'text'
    assert list(text_trace.x) == [0.5]
    assert list(text_trace.y) == pytest.approx([1.5 + gap_width])
    assert list(text_trace.text) == ['-0.50']
    assert text_trace.textposition == 'middle center'
    assert text_trace.hoverinfo == 'skip'
    assert [annotation.text for annotation in fig.layout.annotations] == [
        'Refined parameter correlation matrix',
        'phase.<br>scale',
        'phase.<br>cell.<br>length_c',
        'phase.<br>scale',
        'phase.<br>cell.<br>length_c',
    ]
    assert fig.layout.annotations[0].font.size == POSTERIOR_PAIR_TITLE_FONT_SIZE
    assert fig.layout.annotations[0].yshift == SQUARE_MATRIX_TITLE_YSHIFT_PIXELS
    assert fig.layout.annotations[0].xshift == -Plotter._square_matrix_title_left_shift([
        'phase.<br>scale',
        'phase.<br>cell.<br>length_c',
    ])
    assert fig.layout.margin.t == SQUARE_MATRIX_TOP_MARGIN_PIXELS
    assert fig.layout.margin.b == (
        SQUARE_MATRIX_BOTTOM_MARGIN_PIXELS + 2 * SQUARE_MATRIX_AXIS_TITLE_LINE_HEIGHT_PIXELS
    )
    correlation_wrapper_meta = Plotter._square_matrix_layout_meta(
        n_parameters=2,
        annotation_labels=[
            'phase.<br>scale',
            'phase.<br>cell.<br>length_c',
            'phase.<br>scale',
            'phase.<br>cell.<br>length_c',
        ],
        cell_size_pixels=Plotter._correlation_cell_size_pixels(),
        cap_width=True,
    )['fixed_aspect_wrapper']
    assert (
        fig.layout.meta['fixed_aspect_wrapper']['aspect_ratio']
        == correlation_wrapper_meta['aspect_ratio']
    )
    # Cells are capped to ~16 label characters wide via the wrapper max-width.
    assert (
        fig.layout.meta['fixed_aspect_wrapper']['max_width_pixels']
        == correlation_wrapper_meta['max_width_pixels']
    )
    theme_sync = fig.layout.meta['ed_plotly_theme_sync']
    assert theme_sync['correlation_heatmap'] is True
    assert theme_sync['axis_frame_shape_indexes'] == list(range(len(fig.layout.shapes)))
    assert fig.layout.xaxis.showline is False
    assert fig.layout.xaxis.mirror is False
    assert fig.layout.yaxis.showline is False
    assert fig.layout.yaxis.mirror is False
    assert fig.layout.xaxis.showticklabels is False
    assert fig.layout.yaxis.showticklabels is False
    assert fig.layout.xaxis.title.text is None
    assert fig.layout.yaxis.title.text is None
    assert fig.layout.paper_bgcolor is None
    assert fig.layout.plot_bgcolor is None
    assert len(fig.layout.shapes) == 3
    assert all(shape.type == 'rect' for shape in fig.layout.shapes)
    assert {shape.line.color for shape in fig.layout.shapes} == {
        plotly_mod.PlotlyPlotter._axis_frame_color(),
    }


def test_plot_param_correlations_plotly_labels_respect_threshold(monkeypatch):
    import easydiffraction.display.plotters.plotly as plotly_mod
    from easydiffraction.display.plotting import Plotter

    captured = {}

    def fake_show_figure(self, fig):
        captured['fig'] = fig

    monkeypatch.setattr(plotly_mod.PlotlyPlotter, '_show_figure', fake_show_figure)

    class Param:
        def __init__(self, uid, unique_name):
            self._minimizer_uid = uid
            self.unique_name = unique_name

    class RawResult:
        covar = None
        var_names = ['p1', 'p2', 'p3', 'p4', 'p5']

        class ParamResult:
            def __init__(self, correl):
                self.correl = correl

        params = {
            'p1': ParamResult({'p4': 0.02, 'p5': 0.82}),
            'p2': ParamResult({'p3': -0.91, 'p4': 0.83, 'p5': 0.02}),
            'p3': ParamResult({'p2': -0.91, 'p4': -0.89, 'p5': -0.01}),
            'p4': ParamResult({'p1': 0.02, 'p2': 0.83, 'p3': -0.89, 'p5': 0.01}),
            'p5': ParamResult({'p1': 0.82, 'p2': 0.02, 'p3': -0.01, 'p4': 0.01}),
        }

    class FitResults:
        engine_result = RawResult()
        parameters = [
            Param('p1', 'lbco.cell.length_a'),
            Param('p2', 'hrpt.peak.broad_gauss_u'),
            Param('p3', 'hrpt.peak.broad_gauss_v'),
            Param('p4', 'hrpt.peak.broad_gauss_w'),
            Param('p5', 'hrpt.instrument.twotheta_offset'),
        ]

    class Analysis:
        fit_results = FitResults()

    class Project:
        analysis = Analysis()

    p = Plotter()
    p.engine = 'plotly'
    p._set_project(Project())
    p.plot_param_correlations(threshold=0.7)

    fig = captured['fig']
    heatmap_traces = [trace for trace in fig.data if trace.type == 'heatmap']
    text_traces = [trace for trace in fig.data if trace.type == 'scatter' and trace.mode == 'text']
    assert len(heatmap_traces) == 1
    assert len(text_traces) == 1
    assert list(text_traces[0].text) == ['-0.91', '0.83', '-0.89', '0.82']
    assert len(fig.layout.shapes) == 15


def test_plot_param_correlations_limits_default_table_to_six_parameters(monkeypatch):
    from easydiffraction.display.plotting import Plotter
    from easydiffraction.display.tables import TableRenderer

    captured = {}

    class FakeTabler:
        def render(self, df):
            captured['df'] = df

    monkeypatch.setattr(TableRenderer, 'get', staticmethod(FakeTabler))

    class Param:
        def __init__(self, uid, unique_name):
            self._minimizer_uid = uid
            self.unique_name = unique_name

    class RawResult:
        covar = None
        var_names = ['p1', 'p2', 'p3', 'p4', 'p5', 'p6']

        class ParamResult:
            def __init__(self, correl):
                self.correl = correl

        params = {
            'p1': ParamResult({'p2': 0.95}),
            'p2': ParamResult({'p1': 0.95, 'p3': 0.94}),
            'p3': ParamResult({'p2': 0.94, 'p4': 0.93}),
            'p4': ParamResult({'p3': 0.93, 'p5': 0.92}),
            'p5': ParamResult({'p4': 0.92, 'p6': 0.91}),
            'p6': ParamResult({'p5': 0.91}),
        }

    class FitResults:
        engine_result = RawResult()
        parameters = [
            Param('p1', 'phase.scale'),
            Param('p2', 'phase.cell.length_a'),
            Param('p3', 'phase.background'),
            Param('p4', 'phase.profile.u'),
            Param('p5', 'phase.profile.v'),
            Param('p6', 'phase.profile.w'),
        ]

    class Analysis:
        fit_results = FitResults()

    class Project:
        analysis = Analysis()

    p = Plotter()
    p.engine = 'asciichartpy'
    p._set_project(Project())
    p.plot_param_correlations()

    df = captured['df']
    assert [column.strip() for column in df.columns.get_level_values(0)] == [
        'parameter',
        '1',
        '2',
        '3',
        '4',
        '5',
        '6',
    ]
    assert list(df.index) == [0, 1, 2, 3, 4, 5]
    assert list(df.iloc[:, 0]) == [
        'phase.scale',
        'phase.cell.length_a',
        'phase.background',
        'phase.profile.u',
        'phase.profile.v',
        'phase.profile.w',
    ]
    assert df.iloc[0, 1] == ''
    assert _strip_markup(df.iloc[1, 1]).strip() == '0.95'
    assert _strip_markup(df.iloc[2, 2]).strip() == '0.94'
    assert _strip_markup(df.iloc[3, 3]).strip() == '0.93'
    assert _strip_markup(df.iloc[4, 4]).strip() == '0.92'
    assert _strip_markup(df.iloc[5, 5]).strip() == '0.91'
    assert df.iloc[5, 6] == ''


def test_plot_posterior_pairs_uses_default_max_parameter_limit(monkeypatch):
    from easydiffraction.display.plotting import DEFAULT_CORRELATION_MAX_PARAMETERS
    from easydiffraction.display.plotting import Plotter

    captured: dict[str, object] = {}

    plotter = Plotter()

    def fake_build(self, *, parameters, style, threshold, max_parameters):
        captured['parameters'] = parameters
        captured['style'] = style
        captured['threshold'] = threshold
        captured['max_parameters'] = max_parameters
        return object()

    monkeypatch.setattr(Plotter, '_build_posterior_pairs_plot', fake_build)
    monkeypatch.setattr(Plotter, '_show_plot_figure', lambda self, figure: None)

    plotter.plot_posterior_pairs()

    assert captured['parameters'] is None
    assert captured['style'] == 'auto'
    assert captured['threshold'] is None
    assert captured['max_parameters'] == DEFAULT_CORRELATION_MAX_PARAMETERS


def test_plot_posterior_pairs_prints_title_before_ascii_backend_warning(monkeypatch):
    import easydiffraction.display.plotting as plotting_mod
    from easydiffraction.display.plotting import Plotter

    events: list[tuple[str, str]] = []
    plotter = Plotter()
    plotter.engine = 'asciichartpy'

    monkeypatch.setattr(
        plotting_mod.console, 'paragraph', lambda text: events.append(('title', text))
    )
    monkeypatch.setattr(
        plotting_mod.log, 'warning', lambda message: events.append(('warning', message))
    )

    plotter.plot_posterior_pairs()

    assert events == [
        ('title', 'Posterior pair plot'),
        ('warning', 'Posterior plots currently require the Plotly plotting backend.'),
    ]


def test_plot_param_correlations_shows_full_table_when_threshold_is_zero(monkeypatch):
    from easydiffraction.display.plotting import Plotter
    from easydiffraction.display.tables import TableRenderer

    captured = {}

    class FakeTabler:
        def render(self, df):
            captured['df'] = df

    monkeypatch.setattr(TableRenderer, 'get', staticmethod(FakeTabler))

    class Param:
        def __init__(self, uid, unique_name):
            self._minimizer_uid = uid
            self.unique_name = unique_name

    class RawResult:
        covar = None
        var_names = ['p1', 'p2', 'p3']

        class ParamResult:
            def __init__(self, correl):
                self.correl = correl

        params = {
            'p1': ParamResult({'p2': 0.82}),
            'p2': ParamResult({'p1': 0.82}),
            'p3': ParamResult({'p1': 0.25}),
        }

    class FitResults:
        engine_result = RawResult()
        parameters = [
            Param('p1', 'phase.scale'),
            Param('p2', 'phase.cell.length_a'),
            Param('p3', 'phase.background'),
        ]

    class Analysis:
        fit_results = FitResults()

    class Project:
        analysis = Analysis()

    p = Plotter()
    p.engine = 'asciichartpy'
    p._set_project(Project())
    p.plot_param_correlations(threshold=0)

    df = captured['df']
    assert [column.strip() for column in df.columns.get_level_values(0)] == [
        'parameter',
        '1',
        '2',
        '3',
    ]
    assert list(df.index) == [0, 1, 2]
    assert df.iloc[0, 0] == 'phase.scale'
    assert df.iloc[0, 1] == ''
    assert df.iloc[0, 2] == ''
    assert df.iloc[0, 3] == ''
    assert df.iloc[1, 0] == 'phase.cell.length_a'
    assert _strip_markup(df.iloc[1, 1]).strip() == '0.82'
    assert df.iloc[1, 2] == ''
    assert df.iloc[1, 3] == ''
    assert df.iloc[2, 0] == 'phase.background'
    assert _strip_markup(df.iloc[2, 1]).strip() == '0.25'
    assert _strip_markup(df.iloc[2, 2]).strip() == '0.00'
    assert df.iloc[2, 3] == ''


def test_plot_param_correlations_hides_subthreshold_table_values(monkeypatch):
    from easydiffraction.display.plotting import Plotter
    from easydiffraction.display.tables import TableRenderer

    captured = {}

    class FakeTabler:
        def render(self, df):
            captured['df'] = df

    monkeypatch.setattr(TableRenderer, 'get', staticmethod(FakeTabler))

    class Param:
        def __init__(self, uid, unique_name):
            self._minimizer_uid = uid
            self.unique_name = unique_name

    class RawResult:
        covar = None
        var_names = ['p1', 'p2', 'p3', 'p4', 'p5']

        class ParamResult:
            def __init__(self, correl):
                self.correl = correl

        params = {
            'p1': ParamResult({'p4': 0.02, 'p5': 0.82}),
            'p2': ParamResult({'p3': -0.91, 'p5': 0.02}),
            'p3': ParamResult({'p2': -0.91, 'p4': -0.89, 'p5': -0.01}),
            'p4': ParamResult({'p1': 0.02, 'p3': -0.89, 'p5': 0.01}),
            'p5': ParamResult({'p1': 0.82, 'p2': 0.02, 'p3': -0.01, 'p4': 0.01}),
        }

    class FitResults:
        engine_result = RawResult()
        parameters = [
            Param('p1', 'lbco.cell.length_a'),
            Param('p2', 'hrpt.peak.broad_gauss_u'),
            Param('p3', 'hrpt.peak.broad_gauss_v'),
            Param('p4', 'hrpt.peak.broad_gauss_w'),
            Param('p5', 'hrpt.instrument.twotheta_offset'),
        ]

    class Analysis:
        fit_results = FitResults()

    class Project:
        analysis = Analysis()

    p = Plotter()
    p.engine = 'asciichartpy'
    p._set_project(Project())
    p.plot_param_correlations(threshold=0.7, show_diagonal=False)

    df = captured['df']
    assert [column.strip() for column in df.columns.get_level_values(0)] == [
        'parameter',
        '1',
        '2',
        '3',
        '4',
    ]
    assert list(df.index) == [0, 1, 2, 3, 4]
    assert df.iloc[0, 1] == ''
    assert df.iloc[1, 1] == ''
    assert df.iloc[2, 1] == ''
    assert _strip_markup(df.iloc[2, 2]).strip() == '-0.91'
    assert df.iloc[3, 1] == ''
    assert df.iloc[3, 2] == ''
    assert _strip_markup(df.iloc[3, 3]).strip() == '-0.89'
    assert _strip_markup(df.iloc[4, 1]).strip() == '0.82'
    assert df.iloc[4, 2] == ''
    assert df.iloc[4, 3] == ''
    assert df.iloc[4, 4] == ''


def test_plot_param_correlations_threshold_validation():
    from easydiffraction.display.plotting import Plotter

    with pytest.raises(ValueError, match='between 0 and 1'):
        Plotter._filter_correlation_dataframe(object(), threshold=1.1)
