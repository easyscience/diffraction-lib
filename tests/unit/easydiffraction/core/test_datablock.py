# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause


def test_datablock_collection_add_and_filters_with_real_parameters():
    from easydiffraction.core.category import CategoryItem
    from easydiffraction.core.datablock import DatablockCollection
    from easydiffraction.core.datablock import DatablockItem
    from easydiffraction.core.validation import AttributeSpec
    from easydiffraction.core.variable import Parameter
    from easydiffraction.io.cif.handler import CifHandler

    class Cat(CategoryItem):
        def __init__(self):
            super().__init__()
            self._identity.category_code = 'cat'
            self._identity.category_entry_name = 'e1'
            # real Parameters
            self._p1 = Parameter(
                name='p1',
                description='',
                value_spec=AttributeSpec(default=0.0),
                units='',
                cif_handler=CifHandler(names=['_cat.p1']),
            )
            self._p2 = Parameter(
                name='p2',
                description='',
                value_spec=AttributeSpec(default=0.0),
                units='',
                cif_handler=CifHandler(names=['_cat.p2']),
            )
            # Set actual values via setter
            self._p1.value = 1.0
            self._p2.value = 2.0
            # Make p2 user constrained and not free
            self._p2._user_constrained = True
            self._p2._free = False
            # Mark p1 free to be included in free_parameters
            self._p1.free = True

        @property
        def p1(self):
            return self._p1

        @property
        def p2(self):
            return self._p2

    class Block(DatablockItem):
        def __init__(self, name):
            super().__init__()
            # set datablock entry name
            self._identity.datablock_entry_name = lambda: name
            # include the category as attribute so DatablockItem.parameters picks them up
            self._cat = Cat()

        @property
        def cat(self):
            return self._cat

    coll = DatablockCollection(item_type=Block)
    a = Block('A')
    b = Block('B')
    coll.add(a)
    coll.add(b)
    # parameters collection aggregates from both blocks (p1 & p2 each)
    params = coll.parameters
    assert len(params) == 4
    # fittable excludes user-constrained parameters
    fittable = coll.fittable_parameters
    assert all(isinstance(p, Parameter) for p in fittable)
    assert len(fittable) == 2  # only p1 from each block
    # free is subset of fittable where free=True (true for p1)
    free_params = coll.free_parameters
    assert free_params == fittable


def test_datablock_collection_fittable_excludes_symmetry_constrained_parameters():
    from easydiffraction.core.category import CategoryItem
    from easydiffraction.core.datablock import DatablockCollection
    from easydiffraction.core.datablock import DatablockItem
    from easydiffraction.core.validation import AttributeSpec
    from easydiffraction.core.variable import Parameter
    from easydiffraction.io.cif.handler import CifHandler

    class Cat(CategoryItem):
        def __init__(self):
            super().__init__()
            self._identity.category_code = 'cat'
            self._identity.category_entry_name = 'e1'
            self._free_param = Parameter(
                name='free_param',
                description='',
                value_spec=AttributeSpec(default=0.0),
                units='',
                cif_handler=CifHandler(names=['_cat.free_param']),
            )
            self._fixed_param = Parameter(
                name='fixed_param',
                description='',
                value_spec=AttributeSpec(default=0.0),
                units='',
                cif_handler=CifHandler(names=['_cat.fixed_param']),
            )
            self._free_param.value = 1.0
            self._fixed_param.value = 2.0
            self._free_param.free = True
            self._fixed_param._set_symmetry_constrained(value=True)

        @property
        def free_param(self):
            return self._free_param

        @property
        def fixed_param(self):
            return self._fixed_param

    class Block(DatablockItem):
        def __init__(self, name):
            super().__init__()
            self._identity.datablock_entry_name = lambda: name
            self._cat = Cat()

        @property
        def cat(self):
            return self._cat

    coll = DatablockCollection(item_type=Block)
    coll.add(Block('A'))

    fittable = coll.fittable_parameters

    assert all(isinstance(p, Parameter) for p in fittable)
    assert [p.name for p in fittable] == ['free_param']


def test_datablock_item_help(capsys):
    from easydiffraction.core.category import CategoryItem
    from easydiffraction.core.datablock import DatablockItem
    from easydiffraction.core.validation import AttributeSpec
    from easydiffraction.core.variable import Parameter
    from easydiffraction.io.cif.handler import CifHandler

    class Cat(CategoryItem):
        def __init__(self):
            super().__init__()
            self._identity.category_code = 'cat'
            self._identity.category_entry_name = 'e1'
            self._p1 = Parameter(
                name='p1',
                description='',
                value_spec=AttributeSpec(default=0.0),
                units='',
                cif_handler=CifHandler(names=['_cat.p1']),
            )

        @property
        def p1(self):
            return self._p1

    class Block(DatablockItem):
        def __init__(self):
            super().__init__()
            self._identity.datablock_entry_name = lambda: 'blk'
            self._cat = Cat()

        @property
        def cat(self):
            return self._cat

    b = Block()
    b.help()
    out = capsys.readouterr().out
    assert 'Help for' in out
    assert 'Categories' in out
    assert 'cat' in out


def test_datablock_collection_help(capsys):
    from easydiffraction.core.datablock import DatablockCollection
    from easydiffraction.core.datablock import DatablockItem

    class Block(DatablockItem):
        def __init__(self, name):
            super().__init__()
            self._identity.datablock_entry_name = lambda: name

    coll = DatablockCollection(item_type=Block)
    a = Block('A')
    coll.add(a)
    coll.help()
    out = capsys.readouterr().out
    assert 'Items (1)' in out
    assert 'A' in out
