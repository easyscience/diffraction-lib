# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""
Fitting category item.

Stores the active minimizer as a CIF-serializable descriptor.
"""

from __future__ import annotations

from easydiffraction.analysis.categories.fitting.factory import FittingFactory
from easydiffraction.analysis.fitting import Fitter
from easydiffraction.analysis.minimizers.enums import MinimizerTypeEnum
from easydiffraction.analysis.minimizers.factory import MinimizerFactory
from easydiffraction.core.category import CategoryItem
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import MembershipValidator
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.io.cif.handler import CifHandler
from easydiffraction.utils.logging import console
from easydiffraction.utils.logging import log
from easydiffraction.utils.utils import render_table


@FittingFactory.register
class Fitting(CategoryItem):
    """
    Analysis fitting configuration category.

    Holds the active minimizer backend tag.
    """

    type_info = TypeInfo(
        tag='default',
        description='Fitting configuration category',
    )

    def __init__(self) -> None:
        super().__init__()

        self._minimizer_type: StringDescriptor = StringDescriptor(
            name='minimizer_type',
            description='Fitting minimizer backend type',
            value_spec=AttributeSpec(
                default=MinimizerTypeEnum.default().value,
                validator=MembershipValidator(
                    allowed=[member.value for member in MinimizerTypeEnum]
                ),
            ),
            cif_handler=CifHandler(names=['_fitting.minimizer_type']),
        )

        self._identity.category_code = 'fitting'

    @property
    def minimizer_type(self) -> StringDescriptor:
        """Fitting minimizer backend type."""
        return self._minimizer_type

    @minimizer_type.setter
    def minimizer_type(self, value: str) -> None:
        new_fitter = Fitter(value)
        self._minimizer_type.value = value
        parent = getattr(self, '_parent', None)
        if parent is None:
            return
        parent.fitter = new_fitter
        console.paragraph('Current minimizer changed to')
        console.print(self._minimizer_type.value)

    @property
    def minimizer(self) -> object | None:
        """Live minimizer backend instance, if attached to Analysis."""
        parent = getattr(self, '_parent', None)
        if parent is None or getattr(parent, 'fitter', None) is None:
            return None
        return parent.fitter.minimizer

    def show_minimizer_types(self) -> None:
        """Print supported minimizers and mark the current selection."""
        current = self.minimizer_type.value
        supported = MinimizerFactory.supported_tags()
        all_classes = MinimizerFactory._supported_map()
        columns_data = [
            ['*' if tag == current else '', tag, cls.type_info.description]
            for tag, cls in all_classes.items()
            if tag in supported
        ]
        console.paragraph('Minimizer types')
        render_table(
            columns_headers=['', 'Type', 'Description'],
            columns_alignment=['left', 'left', 'left'],
            columns_data=columns_data,
        )

    @staticmethod
    def show_available_minimizers() -> None:
        """Print available minimizer drivers on this system."""
        MinimizerFactory.show_supported()

    @property
    def as_cif(self) -> str:
        """Return CIF representation of this fitting category."""
        return super().as_cif

    def from_cif(self, block: object, idx: int = 0) -> None:
        """
        Populate this fitting configuration from a CIF block.

        Parameters
        ----------
        block : object
            Parsed CIF block.
        idx : int, default=0
            Row index for loop-like callers; unused for this category.
        """
        super().from_cif(block, idx)
        parent = getattr(self, '_parent', None)
        if parent is None:
            return
        try:
            parent.fitter = Fitter(self._minimizer_type.value)
        except ValueError as error:
            log.warning(str(error))
