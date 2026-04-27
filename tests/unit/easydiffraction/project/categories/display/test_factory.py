# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

import pytest


def test_display_factory_default_and_create():
    from easydiffraction.project.categories.display.default import Display
    from easydiffraction.project.categories.display.factory import DisplayFactory

    assert DisplayFactory.default_tag() == 'default'
    assert 'default' in DisplayFactory.supported_tags()

    display = DisplayFactory.create('default')

    assert isinstance(display, Display)


def test_display_factory_rejects_unknown_tag():
    from easydiffraction.project.categories.display.factory import DisplayFactory

    with pytest.raises(ValueError, match=r"Unsupported type: 'missing'"):
        DisplayFactory.create('missing')
