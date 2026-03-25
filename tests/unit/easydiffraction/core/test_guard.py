# SPDX-FileCopyrightText: 2021-2026 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

import pytest


def test_guard_allows_only_declared_public_properties_and_links_parent(monkeypatch):
    from easydiffraction.core.guard import GuardedBase

    class Child(GuardedBase):
        @property
        def parameters(self):
            return []

        @property
        def as_cif(self) -> str:
            return ''

        @property
        def value(self):
            return getattr(self, '_value', 0)

        @value.setter
        def value(self, v):
            self._assign_attr('_value', v)

    class Parent(GuardedBase):
        def __init__(self):
            super().__init__()
            self._child = Child()

        @property
        def child(self):
            return self._child

        @property
        def parameters(self):
            return []

        @property
        def as_cif(self) -> str:
            return ''

    p = Parent()
    # Writable property on child should set and link parent
    p.child.value = 3
    assert p.child.value == 3
    # Private assign links parent automatically
    assert p.child._parent is p

    # Unknown attribute should raise AttributeError under current logging mode
    with pytest.raises(AttributeError):
        p.child.unknown_attr = 1


def test_help_lists_public_properties(capsys):
    from easydiffraction.core.guard import GuardedBase

    class Obj(GuardedBase):
        @property
        def parameters(self):
            return []

        @property
        def as_cif(self) -> str:
            return ''

        @property
        def name(self):
            """Human-readable name."""
            return 'test'

        @property
        def score(self):
            """Computed score."""
            return 42

        @score.setter
        def score(self, v):
            pass

    obj = Obj()
    obj.help()
    out = capsys.readouterr().out
    assert "Help for 'Obj'" in out
    assert 'name' in out
    assert 'score' in out
    assert 'Properties' in out
    assert 'Methods' in out
    assert '✓' in out  # score is writable
    assert '✗' in out  # name is read-only


def test_first_sentence_extracts_first_paragraph():
    from easydiffraction.core.guard import GuardedBase

    assert GuardedBase._first_sentence(None) == ''
    assert GuardedBase._first_sentence('') == ''
    assert GuardedBase._first_sentence('One liner.') == 'One liner.'
    assert GuardedBase._first_sentence('First.\n\nSecond.') == 'First.'
    assert GuardedBase._first_sentence('Line one\ncontinued.') == 'Line one continued.'
