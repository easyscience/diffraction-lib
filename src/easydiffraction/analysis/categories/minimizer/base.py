# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Base class for persisted minimizer category items."""

from __future__ import annotations

from typing import ClassVar

from easydiffraction.analysis.categories.fit_result.base import FitResultBase
from easydiffraction.analysis.minimizers.enums import MinimizerTypeEnum
from easydiffraction.core.category import CategoryItem
from easydiffraction.core.switchable import SwitchableCategoryBase
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import MembershipValidator
from easydiffraction.core.variable import GenericDescriptorBase
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.io.cif.handler import CifHandler


class MinimizerCategoryBase(CategoryItem, SwitchableCategoryBase):
    """Base class for persisted minimizer settings and results."""

    _category_code = 'minimizer'
    _owner_attr_name = 'minimizer'
    _swap_method_name = '_swap_minimizer'
    _native_key_map: ClassVar[dict[str, str]] = {}
    _setting_descriptor_names: ClassVar[tuple[str, ...]] = ()
    _result_descriptor_names: ClassVar[tuple[str, ...]] = ()
    _fit_result_class: ClassVar[type[FitResultBase]] = FitResultBase

    def __init__(self) -> None:
        super().__init__()
        self._type = StringDescriptor(
            name='type',
            description='Minimizer category type.',
            value_spec=AttributeSpec(
                default=str(self.type_info.tag),
                validator=MembershipValidator(
                    allowed=[member.value for member in MinimizerTypeEnum],
                ),
            ),
            cif_handler=CifHandler(names=['_minimizer.type']),
        )

    @staticmethod
    def _supported_types(
        filters: dict[str, object],
    ) -> list[tuple[str, str]]:
        """Return minimizer types supported by the factory."""
        del filters
        from easydiffraction.analysis.categories.minimizer.factory import (  # noqa: PLC0415
            MinimizerCategoryFactory,
        )

        return [
            (str(tag), klass.type_info.description)
            for tag, klass in MinimizerCategoryFactory._supported_map().items()
        ]

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
            Descriptor values mapped from public minimizer attributes to
            backend-specific keyword names.
        """
        kwargs: dict[str, object] = {}
        for attr_name, native_key in self._native_key_map.items():
            attr = getattr(self, attr_name)
            if isinstance(attr, GenericDescriptorBase):
                kwargs[native_key] = attr.value
            else:
                kwargs[native_key] = attr
        return kwargs
