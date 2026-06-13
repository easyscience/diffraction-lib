# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for display/links.py."""


def test_table_link_behaves_like_visible_text():
    from easydiffraction.display.links import TableLink

    cell = TableLink('length_a', 'https://example.test/docs', title='Docs')

    assert cell == 'length_a'
    assert str(cell) == 'length_a'
    assert cell.text == 'length_a'
    assert cell.url == 'https://example.test/docs'
    assert cell.title == 'Docs'


def test_parameter_docs_link_uses_parameter_url():
    from easydiffraction.display.links import TableLink
    from easydiffraction.display.links import parameter_docs_link

    class Parameter:
        name = 'length_a'
        url = 'https://example.test/docs'

    cell = parameter_docs_link(Parameter())

    assert isinstance(cell, TableLink)
    assert cell == 'length_a'
    assert cell.url == 'https://example.test/docs'


def test_parameter_docs_link_falls_back_to_plain_name():
    from easydiffraction.display.links import parameter_docs_link

    class Parameter:
        name = 'length_a'

    assert parameter_docs_link(Parameter()) == 'length_a'
