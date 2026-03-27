# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause


def test_module_import():
    import easydiffraction.display.plotters.plotly as MUT

    expected_module_name = 'easydiffraction.display.plotters.plotly'
    actual_module_name = MUT.__name__
    assert expected_module_name == actual_module_name


def test_get_trace_and_plot(monkeypatch):
    import easydiffraction.display.plotters.plotly as pp

    # Arrange: force non-PyCharm branch and stub fig.show/HTML/display so nothing opens
    monkeypatch.setattr(pp, 'in_pycharm', lambda: False)

    shown = {'count': 0}

    class DummyFig:
        def update_xaxes(self, **kwargs):
            pass

        def update_yaxes(self, **kwargs):
            pass

        def show(self, **kwargs):
            shown['count'] += 1

    # Patch go.Scatter and go.Figure to minimal dummies
    class DummyScatter:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class DummyGO:
        class Scatter(DummyScatter):
            pass

        class Figure(DummyFig):
            def __init__(self, data=None, layout=None):
                self.data = data
                self.layout = layout

        class Layout:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

    class DummyPIO:
        @staticmethod
        def to_html(fig, include_plotlyjs=None, full_html=None, config=None):
            return '<div>plot</div>'

    dummy_display_calls = {'count': 0}

    def dummy_display(obj):
        dummy_display_calls['count'] += 1

    class DummyHTML:
        def __init__(self, html):
            self.html = html

    monkeypatch.setattr(pp, 'go', DummyGO)
    monkeypatch.setattr(pp, 'pio', DummyPIO)
    monkeypatch.setattr(pp, 'display', dummy_display)
    monkeypatch.setattr(pp, 'HTML', DummyHTML)

    plotter = pp.PlotlyPlotter()

    # Exercise _get_powder_trace
    x = [0, 1, 2]
    y = [1, 2, 3]
    trace = plotter._get_powder_trace(x, y, label='calc')
    assert hasattr(trace, 'kwargs')
    assert trace.kwargs['x'] == x and trace.kwargs['y'] == y

    # Exercise plot_powder (non-PyCharm, display path)
    plotter.plot_powder(
        x,
        y_series=[y],
        labels=['calc'],
        axes_labels=['x', 'y'],
        title='t',
        height=None,
    )

    # One HTML display call expected
    assert dummy_display_calls['count'] == 1 or shown['count'] == 1


def test_plotly_single_crystal_trace_and_plot(monkeypatch):
    import easydiffraction.display.plotters.plotly as pp

    # Arrange: force non-PyCharm branch
    monkeypatch.setattr(pp, 'in_pycharm', lambda: False)

    shown = {'count': 0}

    class DummyFig:
        def update_xaxes(self, **kwargs):
            pass

        def update_yaxes(self, **kwargs):
            pass

        def show(self, **kwargs):
            shown['count'] += 1

    class DummyScatter:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class DummyGO:
        class Scatter(DummyScatter):
            pass

        class Figure(DummyFig):
            def __init__(self, data=None, layout=None):
                self.data = data
                self.layout = layout

        class Layout:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

    class DummyPIO:
        @staticmethod
        def to_html(fig, include_plotlyjs=None, full_html=None, config=None):
            return '<div>plot</div>'

    dummy_display_calls = {'count': 0}

    def dummy_display(obj):
        dummy_display_calls['count'] += 1

    class DummyHTML:
        def __init__(self, html):
            self.html = html

    monkeypatch.setattr(pp, 'go', DummyGO)
    monkeypatch.setattr(pp, 'pio', DummyPIO)
    monkeypatch.setattr(pp, 'display', dummy_display)
    monkeypatch.setattr(pp, 'HTML', DummyHTML)

    plotter = pp.PlotlyPlotter()

    # Exercise _get_single_crystal_trace
    x_calc = [1.0, 2.0, 3.0]
    y_meas = [1.1, 1.9, 3.2]
    y_meas_su = [0.1, 0.1, 0.1]
    trace = plotter._get_single_crystal_trace(x_calc, y_meas, y_meas_su)
    assert hasattr(trace, 'kwargs')
    assert trace.kwargs['x'] == x_calc
    assert trace.kwargs['y'] == y_meas
    assert trace.kwargs['mode'] == 'markers'
    assert 'error_y' in trace.kwargs

    # Exercise _get_diagonal_shape
    shape = plotter._get_diagonal_shape()
    assert shape['type'] == 'line'
    assert shape['xref'] == 'paper'
    assert shape['yref'] == 'paper'

    # Exercise plot_single_crystal
    plotter.plot_single_crystal(
        x_calc=x_calc,
        y_meas=y_meas,
        y_meas_su=y_meas_su,
        axes_labels=['F²calc', 'F²meas'],
        title='SC Test',
        height=None,
    )
    # One display call expected
    assert dummy_display_calls['count'] == 1 or shown['count'] == 1
