# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

import gemmi


def test_table_defaults():
    from easydiffraction.display.tables import TableEngineEnum
    from easydiffraction.project.categories.table.default import Table

    table = Table()

    assert table.type_info.tag == 'default'
    assert table._identity.category_code == 'table'
    assert table.type == 'auto'
    assert table.tabler.engine in [member.value for member in TableEngineEnum]


def test_table_selector_updates_engine():
    from easydiffraction.display.tables import TableEngineEnum
    from easydiffraction.project.categories.table.default import Table

    table = Table()

    table._set_type('rich')

    assert table.type == 'rich'
    assert table.tabler.engine == 'rich'

    table._set_type('auto')

    assert table.type == 'auto'
    assert table.tabler.engine == TableEngineEnum.default().value


def test_table_from_cif_restores_type():
    from easydiffraction.project.categories.table.default import Table

    table = Table()
    block = gemmi.cif.read_string(
        'data_test\n_table.type rich\n',
    ).sole_block()

    table.from_cif(block)

    assert table.type == 'rich'
