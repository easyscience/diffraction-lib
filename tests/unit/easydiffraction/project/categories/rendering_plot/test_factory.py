# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

import pytest


def test_rendering_plot_factory_default_and_create():
    from easydiffraction.project.categories.rendering_plot.default import RenderingPlot
    from easydiffraction.project.categories.rendering_plot.factory import RenderingPlotFactory

    assert RenderingPlotFactory.default_tag() == 'default'
    assert 'default' in RenderingPlotFactory.supported_tags()

    rendering_plot = RenderingPlotFactory.create('default')

    assert isinstance(rendering_plot, RenderingPlot)


def test_rendering_plot_factory_rejects_unknown_tag():
    from easydiffraction.project.categories.rendering_plot.factory import RenderingPlotFactory

    with pytest.raises(ValueError, match=r"Unsupported type: 'missing'"):
        RenderingPlotFactory.create('missing')
