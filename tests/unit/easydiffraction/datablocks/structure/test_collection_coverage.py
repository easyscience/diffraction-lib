# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for Structures collection."""

from easydiffraction.datablocks.structure.collection import Structures
from easydiffraction.datablocks.structure.item.base import Structure


class TestStructuresCollection:
    def test_empty_on_init(self):
        structs = Structures()
        assert len(structs) == 0
        assert structs.names == []

    def test_create(self):
        structs = Structures()
        structs.create(name='s1')
        assert len(structs) == 1
        assert 's1' in structs.names

    def test_create_multiple(self):
        structs = Structures()
        structs.create(name='s1')
        structs.create(name='s2')
        assert len(structs) == 2
        assert 's1' in structs.names
        assert 's2' in structs.names

    def test_add_pre_built(self):
        structs = Structures()
        s = Structure(name='manual')
        structs.add(s)
        assert 'manual' in structs.names

    def test_show_names(self, capsys):
        structs = Structures()
        structs.create(name='alpha')
        structs.show_names()
        out = capsys.readouterr().out
        assert 'Defined structures' in out

    def test_show_params(self, capsys):
        structs = Structures()
        structs.create(name='p1')
        structs.show_params()
        # Should not raise; just exercise the code path
        capsys.readouterr()

    def test_remove(self):
        structs = Structures()
        structs.create(name='rem')
        assert len(structs) == 1
        structs.remove('rem')
        assert len(structs) == 0
