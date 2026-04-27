# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

import gemmi


def test_display_defaults():
    from easydiffraction.project.categories.display.default import Display

    display = Display()

    assert display.type_info.tag == 'default'
    assert display._identity.category_code == 'display'
    assert display.plotter_type.value == display.plotter.engine
    assert display.tabler_type.value == display.tabler.engine


def test_display_plotter_binds_parent():
    from easydiffraction.project.categories.display.default import Display

    display = Display()
    parent = object()
    display._parent = parent

    plotter = display.plotter

    assert plotter._project is parent


def test_display_setters_update_engines():
    from easydiffraction.project.categories.display.default import Display

    display = Display()

    display.plotter_type = 'plotly'
    display.tabler_type = 'rich'

    assert display.plotter_type.value == 'plotly'
    assert display.plotter.engine == 'plotly'
    assert display.tabler_type.value == 'rich'
    assert display.tabler.engine == 'rich'


def test_display_from_cif_restores_types():
    from easydiffraction.project.categories.display.default import Display

    display = Display()
    block = gemmi.cif.read_string(
        'data_test\n_display.plotter_type plotly\n_display.tabler_type rich\n',
    ).sole_block()

    display.from_cif(block)

    assert display.plotter_type.value == 'plotly'
    assert display.tabler_type.value == 'rich'
