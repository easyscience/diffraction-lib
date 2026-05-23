# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Base class for persisted minimizer category items."""

from __future__ import annotations

from typing import ClassVar

from easydiffraction.core.category import CategoryItem
from easydiffraction.core.variable import GenericDescriptorBase


class MinimizerCategoryBase(CategoryItem):
    """Base class for persisted minimizer settings and results."""

    _category_code = 'minimizer'
    _native_key_map: ClassVar[dict[str, str]] = {}
    _setting_descriptor_names: ClassVar[tuple[str, ...]] = ()
    _result_descriptor_names: ClassVar[tuple[str, ...]] = ()

    def _descriptor_values(self, names: tuple[str, ...]) -> dict[str, object]:
        """Return descriptor values for the named public attributes."""
        values: dict[str, object] = {}
        for name in names:
            descriptor = getattr(self, name)
            if isinstance(descriptor, GenericDescriptorBase):
                values[name] = descriptor.value
            else:
                values[name] = descriptor
        return values

    def _reset_result_descriptors(self) -> None:
        """Reset fit-result descriptors to their declared defaults."""
        for name in self._result_descriptor_names:
            descriptor = getattr(self, name)
            if isinstance(descriptor, GenericDescriptorBase):
                descriptor.value = descriptor._value_spec.default_value()

    def _native_kwargs(self) -> dict[str, object]:
        """
        Return backend keyword arguments keyed by native names.

        Returns
        -------
        dict[str, object]
            Descriptor values mapped from public minimizer attributes
            to backend-specific keyword names.

        Raises
        ------
        AttributeError
            If a declared native-key mapping references a missing
            minimizer attribute.
        """
        kwargs: dict[str, object] = {}
        for attr_name, native_key in self._native_key_map.items():
            attr = getattr(self, attr_name)
            if isinstance(attr, GenericDescriptorBase):
                kwargs[native_key] = attr.value
            else:
                kwargs[native_key] = attr
        return kwargs
