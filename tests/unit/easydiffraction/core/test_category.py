# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from easydiffraction.core.category import CategoryCollection
from easydiffraction.core.category import CategoryItem
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.io.cif.handler import CifHandler


class SimpleItem(CategoryItem):
    def __init__(self):
        super().__init__()
        self._identity.category_code = 'simple'
        object.__setattr__(
            self,
            '_a',
            StringDescriptor(
                name='a',
                description='',
                value_spec=AttributeSpec(default='_'),
                cif_handler=CifHandler(names=['_simple.a']),
            ),
        )
        object.__setattr__(
            self,
            '_b',
            StringDescriptor(
                name='b',
                description='',
                value_spec=AttributeSpec(default='_'),
                cif_handler=CifHandler(names=['_simple.b']),
            ),
        )
        self._identity.category_entry_name = lambda: str(self._a.value)

    @property
    def a(self):
        return self._a

    @a.setter
    def a(self, value):
        self._a.value = value

    @property
    def b(self):
        return self._b

    @b.setter
    def b(self, value):
        self._b.value = value


class SimpleCollection(CategoryCollection):
    def __init__(self):
        super().__init__(item_type=SimpleItem)


def test_category_item_str_and_properties():
    it = SimpleItem()
    it.a = 'name1'
    s = str(it)
    assert '<' in s and 'a=' in s and 'b=' in s
    assert it.unique_name.endswith('.simple.name1') or it.unique_name == 'simple.name1'
    assert len(it.parameters) == 2


def test_category_collection_str_and_cif_calls():
    c = SimpleCollection()
    c.create(a='n1')
    c.create(a='n2')
    s = str(c)
    assert 'collection' in s and '2 items' in s
    # as_cif delegates to serializer; should be a string (possibly empty)
    assert isinstance(c.as_cif, str)


def test_category_item_help(capsys):
    it = SimpleItem()
    it.a = 'name1'
    it.help()
    out = capsys.readouterr().out
    assert 'Help for' in out
    assert 'Parameters' in out
    assert 'string' in out  # Type column
    assert '✓' in out  # a and b are writable
    assert 'Methods' in out


def test_category_collection_help(capsys):
    c = SimpleCollection()
    c.create(a='n1')
    c.create(a='n2')
    c.help()
    out = capsys.readouterr().out
    assert 'Help for' in out
    assert 'Items (2)' in out
    assert 'n1' in out
    assert 'n2' in out
