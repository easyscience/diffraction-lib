# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

import pytest


def test_table_factory_default_and_create():
    from easydiffraction.project.categories.table.default import Table
    from easydiffraction.project.categories.table.factory import TableFactory

    assert TableFactory.default_tag() == 'default'
    assert 'default' in TableFactory.supported_tags()

    table = TableFactory.create('default')

    assert isinstance(table, Table)


def test_table_factory_rejects_unknown_tag():
    from easydiffraction.project.categories.table.factory import TableFactory

    with pytest.raises(ValueError, match=r"Unsupported type: 'missing'"):
        TableFactory.create('missing')
