# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from types import SimpleNamespace

import pytest

from easydiffraction.core.switchable import SwitchableCategoryBase


class _Switchable(SwitchableCategoryBase):
    _category_code = 'dummy_category'
    _owner_attr_name = 'dummy'
    _swap_method_name = '_swap_dummy'

    def __init__(
        self,
        *,
        current_type: str = 'alpha',
        supported: list[tuple[str, str]] | None = None,
    ) -> None:
        self._type = SimpleNamespace(value=current_type)
        self.supported = supported or [
            ('alpha', 'Alpha type'),
            ('beta', 'Beta type'),
        ]
        self.filters_seen: dict[str, object] | None = None

    def _supported_types(
        self,
        filters: dict[str, object],
    ) -> list[tuple[str, str]]:
        self.filters_seen = filters
        return self.supported


class _CanonicalSwitchable(_Switchable):
    def _canonicalize(self, value: str) -> str:
        return value.lower()


class _Parent:
    def __init__(self, category: _Switchable) -> None:
        self.dummy = category
        self.swap_calls: list[str] = []

    def _supported_filters_for(self, category: object) -> dict[str, object]:
        assert category is self.dummy
        return {'scope': 'test'}

    def _swap_dummy(self, value: str) -> None:
        self.swap_calls.append(value)
        self.dummy._type.value = value


def test_type_setter_rejects_detached_category():
    category = _Switchable()

    with pytest.raises(RuntimeError, match='detached'):
        category.type = 'beta'


def test_type_setter_rejects_stale_category_reference():
    old_category = _Switchable()
    new_category = _Switchable()
    parent = _Parent(new_category)
    old_category._parent = parent

    with pytest.raises(RuntimeError, match='no longer the live category'):
        old_category.type = 'beta'


def test_default_canonicalize_is_identity():
    category = _Switchable()

    assert category._canonicalize('MiXeD') == 'MiXeD'


def test_type_setter_delegates_canonical_value_to_owner():
    category = _CanonicalSwitchable()
    parent = _Parent(category)
    category._parent = parent

    category.type = 'BETA'

    assert parent.swap_calls == ['beta']
    assert category.type == 'beta'


@pytest.mark.parametrize(
    ('supported', 'expected_title'),
    [
        ([('alpha', 'Factory-backed type'), ('beta', 'Other type')], 'Dummy Category types'),
        ([('auto', 'Renderer default'), ('plotly', 'Plotly renderer')], 'Dummy Category types'),
        ([('single', 'Single fit'), ('joint', 'Joint fit')], 'Dummy Category types'),
    ],
)
def test_show_supported_renders_active_type_for_supported_shapes(
    supported,
    expected_title,
    monkeypatch,
):
    import easydiffraction.core.switchable as switchable_mod

    category = _Switchable(current_type=supported[0][0], supported=supported)
    parent = _Parent(category)
    category._parent = parent
    paragraphs: list[str] = []
    rendered: dict[str, object] = {}

    monkeypatch.setattr(
        switchable_mod.console,
        'paragraph',
        paragraphs.append,
    )
    monkeypatch.setattr(
        switchable_mod,
        'render_table',
        lambda **kwargs: rendered.update(kwargs),
    )

    category.show_supported()

    assert paragraphs == [expected_title]
    assert category.filters_seen == {'scope': 'test'}
    assert rendered['columns_headers'] == ['', 'Type', 'Description']
    assert rendered['columns_data'][0][0] == '*'
    assert rendered['columns_data'][0][1:] == list(supported[0])
