# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""
Fit category item.

Stores the active minimizer and fitting mode as CIF-serializable
descriptors and provides the public entry-point for running fits.
"""

from __future__ import annotations

from easydiffraction.analysis.categories.fit.enums import FitModeEnum
from easydiffraction.analysis.categories.fit.factory import FitFactory
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


@FitFactory.register
class Fit(CategoryItem):
    """
    Analysis fitting configuration and execution entry-point.

    Holds the active minimizer backend tag and fit mode value.
    """

    type_info = TypeInfo(
        tag='default',
        description='Fit configuration category',
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
            cif_handler=CifHandler(names=['_fit.minimizer_type']),
        )
        self._mode: StringDescriptor = StringDescriptor(
            name='mode',
            description='Fitting mode',
            value_spec=AttributeSpec(
                default=FitModeEnum.default().value,
                validator=MembershipValidator(allowed=[member.value for member in FitModeEnum]),
            ),
            cif_handler=CifHandler(names=['_fit.mode']),
        )

        self._identity.category_code = 'fit'

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

    @property
    def mode(self) -> StringDescriptor:
        """Fitting mode."""
        return self._mode

    @mode.setter
    def mode(self, value: str) -> None:
        self._mode.value = value

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

    def show_modes(self) -> None:
        """Print supported fit modes and mark the current selection."""
        parent = getattr(self, '_parent', None)
        if parent is None or not getattr(parent, 'project', None):
            modes = [FitModeEnum.SINGLE, FitModeEnum.JOINT, FitModeEnum.SEQUENTIAL]
        else:
            num_expts = len(parent.project.experiments) if parent.project.experiments else 0
            if num_expts <= 1:
                modes = [FitModeEnum.SINGLE]
            else:
                modes = [FitModeEnum.SINGLE, FitModeEnum.JOINT, FitModeEnum.SEQUENTIAL]

        current = self.mode.value
        columns_data = [
            ['*' if mode.value == current else '', mode.value, mode.description()]
            for mode in modes
        ]
        console.paragraph('Fit modes')
        render_table(
            columns_headers=['', 'Type', 'Description'],
            columns_alignment=['left', 'left', 'left'],
            columns_data=columns_data,
        )

    def run(
        self,
        verbosity: str | None = None,
        *,
        use_physical_limits: bool = False,
    ) -> None:
        """
        Execute fitting for the owning analysis.

        Parameters
        ----------
        verbosity : str | None, default=None
            Console output verbosity override.
        use_physical_limits : bool, default=False
            Whether to fall back to physical limits as fit bounds.

        Raises
        ------
        RuntimeError
            If this category is not attached to an Analysis object.
        """
        parent = getattr(self, '_parent', None)
        if parent is None:
            msg = 'Fit category is not attached to an Analysis object.'
            raise RuntimeError(msg)
        parent._run_fit(verbosity=verbosity, use_physical_limits=use_physical_limits)

    def __call__(
        self,
        verbosity: str | None = None,
        *,
        use_physical_limits: bool = False,
    ) -> None:
        """Execute :meth:`run` for convenience."""
        self.run(verbosity=verbosity, use_physical_limits=use_physical_limits)

    def from_cif(self, block: object, idx: int = 0) -> None:
        """
        Populate this fit configuration from a CIF block.

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
