# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Common fit-result status category."""

from __future__ import annotations

from typing import ClassVar

from easydiffraction.analysis.categories.fit_result.factory import FitResultFactory
from easydiffraction.analysis.enums import FitResultKindEnum
from easydiffraction.core.category import CategoryItem
from easydiffraction.core.display_handler import DisplayHandler
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.variable import BoolDescriptor
from easydiffraction.core.variable import EnumDescriptor
from easydiffraction.core.variable import GenericDescriptorBase
from easydiffraction.core.variable import IntegerDescriptor
from easydiffraction.core.variable import NumericDescriptor
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.io.cif.handler import CifHandler


def _result_display_handler(label: str) -> DisplayHandler:
    """
    Return a display handler with the same label for HTML and LaTeX.
    """
    return DisplayHandler(display_name=label, latex_name=label)


@FitResultFactory.register
class FitResultBase(CategoryItem):
    """Common persisted fit-result status metadata."""

    _category_code = 'fit_result'
    _result_descriptor_names: ClassVar[tuple[str, ...]] = (
        'success',
        'message',
        'iterations',
        'fitting_time',
        'reduced_chi_square',
        'result_kind',
    )

    type_info = TypeInfo(
        tag='default',
        description='Common persisted fit-result status metadata',
    )

    def __init__(self) -> None:
        super().__init__()
        self._result_kind = EnumDescriptor(
            name='result_kind',
            enum=FitResultKindEnum,
            description='Kind of the latest persisted fit-result projection.',
            cif_handler=CifHandler(names=['_fit_result.result_kind']),
            display_handler=_result_display_handler('Result kind'),
        )
        self._success = BoolDescriptor(
            name='success',
            description='Whether the latest persisted fit-result projection succeeded.',
            value_spec=AttributeSpec(default=None, allow_none=True),
            cif_handler=CifHandler(names=['_fit_result.success']),
            display_handler=_result_display_handler('Success'),
        )
        self._message = StringDescriptor(
            name='message',
            description='Status message for the latest persisted fit-result projection.',
            value_spec=AttributeSpec(default=None, allow_none=True),
            cif_handler=CifHandler(names=['_fit_result.message']),
            display_handler=_result_display_handler('Message'),
        )
        self._iterations = IntegerDescriptor(
            name='iterations',
            description='Iteration count for the latest persisted fit-result projection.',
            value_spec=AttributeSpec(default=None, allow_none=True),
            cif_handler=CifHandler(names=['_fit_result.iterations']),
            display_handler=_result_display_handler('Iterations'),
        )
        self._fitting_time = NumericDescriptor(
            name='fitting_time',
            description='Fitting time in seconds for the latest persisted projection.',
            value_spec=AttributeSpec(default=None, allow_none=True),
            cif_handler=CifHandler(names=['_fit_result.fitting_time']),
            display_handler=_result_display_handler('Fitting time (s)'),
        )
        self._reduced_chi_square = NumericDescriptor(
            name='reduced_chi_square',
            description='Reduced chi-square for the latest persisted projection.',
            value_spec=AttributeSpec(default=None, allow_none=True),
            cif_handler=CifHandler(names=['_fit_result.reduced_chi_square']),
            display_handler=_result_display_handler('Reduced chi-square'),
        )

    @property
    def result_kind(self) -> EnumDescriptor:
        """Kind of the latest persisted fit-result projection."""
        return self._result_kind

    def _set_result_kind(self, value: str) -> None:
        """Set the result kind for internal callers."""
        self._result_kind.value = value

    @property
    def success(self) -> BoolDescriptor:
        """
        Whether the latest persisted fit-result projection succeeded.
        """
        return self._success

    def _set_success(self, *, value: bool | None) -> None:
        """Set the success flag for internal callers."""
        self._success.value = value

    @property
    def message(self) -> StringDescriptor:
        """
        Status message for the latest persisted fit-result projection.
        """
        return self._message

    def _set_message(self, value: str | None) -> None:
        """Set the fit-result message for internal callers."""
        self._message.value = value

    @property
    def iterations(self) -> IntegerDescriptor:
        """
        Iteration count for the latest persisted fit-result projection.
        """
        return self._iterations

    def _set_iterations(self, value: int | None) -> None:
        """Set the iteration count for internal callers."""
        self._iterations.value = value

    @property
    def fitting_time(self) -> NumericDescriptor:
        """
        Fitting time in seconds for the latest persisted projection.
        """
        return self._fitting_time

    def _set_fitting_time(self, value: float | None) -> None:
        """Set the fitting time for internal callers."""
        self._fitting_time.value = value

    @property
    def reduced_chi_square(self) -> NumericDescriptor:
        """Reduced chi-square for the latest persisted projection."""
        return self._reduced_chi_square

    def _set_reduced_chi_square(self, value: float | None) -> None:
        """Set the reduced chi-square for internal callers."""
        self._reduced_chi_square.value = value

    def _reset_result_descriptors(self) -> None:
        """Reset fit-result descriptors to declared defaults."""
        for name in self._result_descriptor_names:
            descriptor = getattr(self, name)
            if isinstance(descriptor, GenericDescriptorBase):
                descriptor.value = descriptor._value_spec.default_value()
