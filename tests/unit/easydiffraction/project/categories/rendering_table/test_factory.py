# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

import pytest


def test_table_factory_default_and_create():
    from easydiffraction.project.categories.rendering_table.default import RenderingTable
    from easydiffraction.project.categories.rendering_table.factory import RenderingTableFactory

    assert RenderingTableFactory.default_tag() == 'default'
    assert 'default' in RenderingTableFactory.supported_tags()

    table = RenderingTableFactory.create('default')

    assert isinstance(table, RenderingTable)


def test_table_factory_rejects_unknown_tag():
    from easydiffraction.project.categories.rendering_table.factory import RenderingTableFactory

    with pytest.raises(ValueError, match=r"Unsupported type: 'missing'"):
        RenderingTableFactory.create('missing')
