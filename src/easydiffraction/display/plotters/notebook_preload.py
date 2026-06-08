# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Preload the interactive-plot runtime once in live notebooks."""

from __future__ import annotations

from easydiffraction.display.plotters.plotly import PlotlyPlotter
from easydiffraction.utils.environment import in_jupyter


def preload_interactive_runtime() -> None:
    """
    Load the self-hosted Plotly runtime once in a live notebook.

    Imported for its side effect by ``easydiffraction.__init__`` so live
    figures render instantly, without each plot carrying the runtime or
    reserving a blank box. A no-op outside notebooks and in the docs
    build, where the page loads the runtime itself.
    """
    if in_jupyter():
        PlotlyPlotter._inject_runtime_once()


preload_interactive_runtime()
