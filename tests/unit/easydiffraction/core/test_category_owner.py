# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from easydiffraction.core.category import CategoryItem
from easydiffraction.core.category_owner import CategoryOwner
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.variable import Parameter
from easydiffraction.io.cif.handler import CifHandler
from easydiffraction.io.cif.serialize import category_owner_to_cif


class _FastCategory(CategoryItem):
    _update_priority = 1

    def __init__(self, update_calls: list[tuple[str, bool]] | None = None) -> None:
        super().__init__()
        self._identity.category_code = 'fast'
        self._update_calls = update_calls
        self._param = Parameter(
            name='param',
            description='Fast category parameter',
            value_spec=AttributeSpec(default=0.0),
            units='',
            cif_handler=CifHandler(names=['_fast.param']),
        )

    @property
    def param(self) -> Parameter:
        return self._param

    def _update(self, *, called_by_minimizer: bool = False) -> None:
        if self._update_calls is not None:
            self._update_calls.append(('fast', called_by_minimizer))


class _SlowCategory(CategoryItem):
    _update_priority = 20

    def __init__(self, update_calls: list[tuple[str, bool]] | None = None) -> None:
        super().__init__()
        self._identity.category_code = 'slow'
        self._update_calls = update_calls
        self._param = Parameter(
            name='param',
            description='Slow category parameter',
            value_spec=AttributeSpec(default=0.0),
            units='',
            cif_handler=CifHandler(names=['_slow.param']),
        )

    @property
    def param(self) -> Parameter:
        return self._param

    def _update(self, *, called_by_minimizer: bool = False) -> None:
        if self._update_calls is not None:
            self._update_calls.append(('slow', called_by_minimizer))


class _Owner(CategoryOwner):
    def __init__(self, update_calls: list[tuple[str, bool]] | None = None) -> None:
        super().__init__()
        self._slow = _SlowCategory(update_calls)
        self._fast = _FastCategory(update_calls)

    @property
    def fast(self) -> _FastCategory:
        return self._fast

    @property
    def slow(self) -> _SlowCategory:
        return self._slow

    @property
    def as_cif(self) -> str:
        return category_owner_to_cif(self)


class _OwnerWithSerializableSubset(_Owner):
    def _serializable_categories(self) -> list:
        return [self.slow]


def test_category_owner_sorts_categories_and_flattens_parameters():
    owner = _Owner()

    assert owner.fast._parent is owner
    assert owner.slow._parent is owner
    assert [category._identity.category_code for category in owner.categories] == ['fast', 'slow']
    assert [parameter.unique_name for parameter in owner.parameters] == [
        'fast.param',
        'slow.param',
    ]


def test_category_owner_updates_only_when_needed_and_can_force_minimizer_updates():
    update_calls: list[tuple[str, bool]] = []
    owner = _Owner(update_calls)

    owner._update_categories()

    assert update_calls == [('fast', False), ('slow', False)]
    assert owner._need_categories_update is False

    update_calls.clear()
    owner._update_categories()
    assert update_calls == []

    owner._update_categories(called_by_minimizer=True)
    assert update_calls == [('fast', True), ('slow', True)]
    assert owner._need_categories_update is False


def test_category_owner_force_updates_when_not_dirty():
    # force=True bypasses the clean-state short-circuit so an explicit
    # recompute (Analysis.calculate) refreshes categories even when this
    # owner was not itself edited — e.g. a linked structure changed.
    update_calls: list[tuple[str, bool]] = []
    owner = _Owner(update_calls)
    owner._need_categories_update = False

    owner._update_categories(force=True)

    assert update_calls == [('fast', False), ('slow', False)]
    assert owner._need_categories_update is False


def test_category_owner_descriptor_changes_mark_owner_dirty():
    owner = _Owner()
    owner._need_categories_update = False

    owner.fast.param.value = 1.5
    assert owner._need_categories_update is True

    owner._need_categories_update = False
    owner.slow.param._set_value_from_minimizer(2.5)
    assert owner._need_categories_update is True


def test_category_owner_as_cif_respects_serializable_categories_override():
    owner = _OwnerWithSerializableSubset()

    cif_text = owner.as_cif

    assert '_slow.param' in cif_text
    assert '_fast.param' not in cif_text
