# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for the live-notebook interactive-plot runtime preload."""

from easydiffraction.display.plotters import notebook_preload


def test_preload_injects_runtime_in_jupyter(monkeypatch):
    import easydiffraction.display.plotters.plotly as pp

    calls = []
    monkeypatch.setattr(notebook_preload, 'in_jupyter', lambda: True)
    monkeypatch.setattr(
        pp.PlotlyPlotter,
        '_inject_runtime_once',
        classmethod(lambda cls: calls.append('injected')),
    )
    notebook_preload.preload_interactive_runtime()
    assert calls == ['injected']


def test_preload_is_a_noop_outside_jupyter(monkeypatch):
    import easydiffraction.display.plotters.plotly as pp

    calls = []
    monkeypatch.setattr(notebook_preload, 'in_jupyter', lambda: False)
    monkeypatch.setattr(
        pp.PlotlyPlotter,
        '_inject_runtime_once',
        classmethod(lambda cls: calls.append('injected')),
    )
    notebook_preload.preload_interactive_runtime()
    assert calls == []
