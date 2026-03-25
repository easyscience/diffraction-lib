# SPDX-FileCopyrightText: 2021-2026 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

def test_collection_add_get_delete_and_names():
    from easydiffraction.core.collection import CollectionBase
    from easydiffraction.core.identity import Identity

    class Item:
        def __init__(self, name):
            self._identity = Identity(owner=self, category_entry=lambda: name)

    class MyCollection(CollectionBase):
        @property
        def parameters(self):
            return []

        @property
        def as_cif(self) -> str:
            return ''

    c = MyCollection(item_type=Item)
    a = Item('a')
    b = Item('b')
    c['a'] = a
    c['b'] = b
    assert c['a'] is a and c['b'] is b
    a2 = Item('a')
    c['a'] = a2
    assert c['a'] is a2 and len(list(c.keys())) == 2
    del c['b']
    assert list(c.names) == ['a']


def test_collection_contains():
    from easydiffraction.core.collection import CollectionBase
    from easydiffraction.core.identity import Identity

    class Item:
        def __init__(self, name):
            self._identity = Identity(owner=self, category_entry=lambda: name)

    class MyCollection(CollectionBase):
        @property
        def parameters(self):
            return []

        @property
        def as_cif(self) -> str:
            return ''

    c = MyCollection(item_type=Item)
    c['x'] = Item('x')
    assert 'x' in c
    assert 'y' not in c


def test_collection_remove():
    import pytest

    from easydiffraction.core.collection import CollectionBase
    from easydiffraction.core.identity import Identity

    class Item:
        def __init__(self, name):
            self._identity = Identity(owner=self, category_entry=lambda: name)

    class MyCollection(CollectionBase):
        @property
        def parameters(self):
            return []

        @property
        def as_cif(self) -> str:
            return ''

    c = MyCollection(item_type=Item)
    c['a'] = Item('a')
    c['b'] = Item('b')
    c.remove('a')
    assert 'a' not in c
    assert len(c) == 1
    with pytest.raises(KeyError):
        c.remove('nonexistent')


def test_collection_datablock_keyed_items():
    """Verify __setitem__/__delitem__/__contains__ work for datablock-keyed items."""
    from easydiffraction.core.collection import CollectionBase
    from easydiffraction.core.identity import Identity

    class DbItem:
        def __init__(self, name):
            self._identity = Identity(owner=self, datablock_entry=lambda: name)

    class MyCollection(CollectionBase):
        @property
        def parameters(self):
            return []

        @property
        def as_cif(self) -> str:
            return ''

    c = MyCollection(item_type=DbItem)
    a = DbItem('alpha')
    b = DbItem('beta')
    c['alpha'] = a
    c['beta'] = b
    assert 'alpha' in c
    assert c['alpha'] is a

    # Replace
    a2 = DbItem('alpha')
    c['alpha'] = a2
    assert c['alpha'] is a2
    assert len(c) == 2

    # Delete
    del c['beta']
    assert 'beta' not in c
    assert len(c) == 1
