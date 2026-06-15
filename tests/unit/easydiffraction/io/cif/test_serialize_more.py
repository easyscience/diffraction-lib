# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause


def test_datablock_item_to_cif_includes_item_and_collection():
    import easydiffraction.io.cif.serialize as MUT
    from easydiffraction.core.category import CategoryCollection
    from easydiffraction.core.category import CategoryItem
    from easydiffraction.io.cif.handler import TagSpec

    class Item(CategoryItem):
        def __init__(self, val):
            super().__init__()
            self._p = type('P', (), {})()
            self._p._tags = TagSpec(edi_names=['_aa'])
            self._p.value = val

        @property
        def parameters(self):
            return [self._p]

        @property
        def as_cif(self) -> str:
            return MUT.category_item_to_cif(self)

    class DB:
        def __init__(self):
            self._identity = type('I', (), {'datablock_entry_name': 'block1'})()
            # one CategoryItem-like
            self.item = Item(42)
            # one CategoryCollection-like
            self.coll = CategoryCollection(item_type=Item)
            self.coll['row1'] = Item(7)

    out = MUT.datablock_item_to_cif(DB())
    assert out.startswith('data_block1')
    assert '_aa 42' in out
    assert 'loop_' in out
    assert '_aa' in out
    assert '7' in out


def test_datablock_item_to_cif_skips_empty_category_fragments():
    import easydiffraction.io.cif.serialize as MUT
    from easydiffraction.core.category import CategoryCollection
    from easydiffraction.core.category import CategoryItem
    from easydiffraction.io.cif.handler import TagSpec

    class Item(CategoryItem):
        def __init__(self, val):
            super().__init__()
            self._p = type('P', (), {})()
            self._p._tags = TagSpec(edi_names=['_aa'])
            self._p.value = val

        @property
        def parameters(self):
            return [self._p]

        @property
        def as_cif(self) -> str:
            return MUT.category_item_to_cif(self)

    class EmptyItem(CategoryItem):
        @property
        def parameters(self):
            return []

        @property
        def as_cif(self) -> str:
            return ''

    class DB:
        def __init__(self):
            self._identity = type('I', (), {'datablock_entry_name': 'block1'})()
            self.item = Item(42)
            self.empty_item = EmptyItem()
            self.coll = CategoryCollection(item_type=Item)
            self.coll['row1'] = Item(7)
            self.empty_coll = CategoryCollection(item_type=Item)

    out = MUT.datablock_item_to_cif(DB())
    assert out == 'data_block1\n\n_aa 42\n\nloop_\n_aa\n7'
    assert '\n\n\n' not in out


def test_datablock_collection_to_cif_concatenates_blocks():
    import easydiffraction.io.cif.serialize as MUT

    class B:
        def __init__(self, t):
            self._t = t

        @property
        def as_cif(self):
            return self._t

    coll = {'a': B('A'), 'b': B('B')}
    out = MUT.datablock_collection_to_cif(coll)
    assert out == 'A\n\nB'


def test_project_info_to_cif_contains_core_fields():
    import easydiffraction.io.cif.serialize as MUT
    from easydiffraction.project.project_metadata import ProjectMetadata

    metadata = ProjectMetadata(name='p1', title='My Title', description='Some description text')
    out = MUT.project_metadata_to_cif(metadata)
    assert '_metadata.name             p1' in out
    assert '_metadata.title            "My Title"' in out
    assert '_metadata.description      "Some description text"' in out
    assert '_metadata.created          "' in out
    assert '_metadata.last_modified    "' in out


def test_project_info_to_cif_wraps_long_description_as_text_field():
    import easydiffraction.io.cif.serialize as MUT
    from easydiffraction.project.project_metadata import ProjectMetadata

    description = ' '.join(['long'] * 20)
    metadata = ProjectMetadata(name='p1', title='My Title', description=description)

    out = MUT.project_metadata_to_cif(metadata)

    assert '_metadata.description      ' in out
    assert '\n;\n' in out
    assert 'long long long long long long long long long long long long' in out


def test_experiment_to_cif_with_and_without_data():
    import easydiffraction.io.cif.serialize as MUT

    class DS:
        def __init__(self, text):
            self._text = text

        @property
        def as_cif(self):
            return self._text

    class Exp:
        def __init__(self, data_text):
            self._identity = type('I', (), {'datablock_entry_name': 'expA'})()
            self.datastore = DS(data_text)
            # Minimal CategoryItem to be picked up by datablock_item_to_cif
            from easydiffraction.core.category import CategoryItem
            from easydiffraction.io.cif.handler import TagSpec

            class Item(CategoryItem):
                def __init__(self):
                    super().__init__()
                    self._p = type('P', (), {})()
                    self._p._tags = TagSpec(edi_names=['_k'])
                    self._p.value = 1

                @property
                def parameters(self):
                    return [self._p]

                @property
                def as_cif(self):
                    return MUT.category_item_to_cif(self)

            self.item = Item()

    out_with = MUT.experiment_to_cif(Exp('loop_\\n_x\\n1'))
    # Datastore CIF no longer automatically included in experiment CIF output
    assert out_with.startswith('data_expA')
    # Check that item CIF is included
    assert '_k' in out_with
    assert '1' in out_with

    out_without = MUT.experiment_to_cif(Exp(''))
    assert out_without.startswith('data_expA')
    assert out_without.endswith('1')


def test_analysis_to_cif_renders_all_sections(monkeypatch):
    import easydiffraction.io.cif.serialize as MUT

    class Obj:
        def __init__(self, t):
            self._t = t

        @property
        def as_cif(self):
            return self._t

    class A:
        minimizer = Obj('_minimizer.type lmfit')
        aliases = Obj('ALIASES')
        constraints = Obj('CONSTRAINTS')

    monkeypatch.setattr(
        MUT,
        'category_owner_to_cif',
        lambda analysis: (
            f'{analysis.minimizer.as_cif}\n\n'
            f'{analysis.aliases.as_cif}\n\n'
            f'{analysis.constraints.as_cif}'
        ),
    )

    out = MUT.analysis_to_cif(A())
    lines = [line for line in out.splitlines() if line]
    assert lines[0].startswith('_minimizer.type')
    assert 'lmfit' in lines[0]
    assert 'ALIASES' in out
    assert 'CONSTRAINTS' in out
