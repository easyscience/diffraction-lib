# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

import pytest


def test_rendering_factory_default_and_create():
    from easydiffraction.project.categories.rendering.default import Rendering
    from easydiffraction.project.categories.rendering.factory import RenderingFactory

    assert RenderingFactory.default_tag() == 'default'
    assert 'default' in RenderingFactory.supported_tags()

    rendering = RenderingFactory.create('default')

    assert isinstance(rendering, Rendering)


def test_rendering_factory_rejects_unknown_tag():
    from easydiffraction.project.categories.rendering.factory import RenderingFactory

    with pytest.raises(ValueError, match=r"Unsupported type: 'missing'"):
        RenderingFactory.create('missing')
