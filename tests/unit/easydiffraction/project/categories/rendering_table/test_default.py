# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

import gemmi


def test_table_defaults():
    from easydiffraction.display.tables import TableEngineEnum
    from easydiffraction.project.categories.rendering_table.default import RenderingTable

    table = RenderingTable()

    assert table.type_info.tag == 'default'
    assert table._identity.category_code == 'rendering_table'
    assert table.type == 'auto'
    assert table.tabler.engine in [member.value for member in TableEngineEnum]


def test_table_selector_updates_engine():
    from easydiffraction.display.tables import TableEngineEnum
    from easydiffraction.project.categories.rendering_table.default import RenderingTable

    table = RenderingTable()

    table._set_type('rich')

    assert table.type == 'rich'
    assert table.tabler.engine == 'rich'

    table._set_type('auto')

    assert table.type == 'auto'
    assert table.tabler.engine == TableEngineEnum.default().value


def test_table_from_cif_restores_type():
    from easydiffraction.project.categories.rendering_table.default import RenderingTable

    table = RenderingTable()

    swapped: list[tuple[str, dict]] = []

    class _Parent:
        def _swap_rendering_table(self, new_type, *, strict):
            swapped.append((new_type, {'strict': strict}))
            table._set_type(new_type, strict=strict)

    table._parent = _Parent()
    block = gemmi.cif.read_string(
        'data_test\n_rendering_table.type rich\n',
    ).sole_block()

    table.from_cif(block)

    assert swapped == [('rich', {'strict': False})]
    assert table.type == 'rich'


def test_table_invalid_type_assignment_raises():
    import pytest

    from easydiffraction.project.categories.rendering_table.default import RenderingTable

    table = RenderingTable()
    initial_type = table.type

    with pytest.raises(ValueError, match='Unsupported rendering_table type'):
        table._set_type('bogus-engine')

    assert table.type == initial_type
