# SPDX-FileCopyrightText: 2021-2026 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
"""Fit-mode category item.

Stores the active fitting strategy (``'single'`` or ``'joint'``) as a
CIF-serializable descriptor.
"""

from __future__ import annotations

from easydiffraction.core.category import CategoryItem
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import RegexValidator
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.io.cif.handler import CifHandler


class FitMode(CategoryItem):
    """Fitting strategy selector.

    Holds a single ``mode`` descriptor whose value is ``'single'``
    (fit each experiment independently) or ``'joint'`` (fit all
    experiments simultaneously with shared parameters).
    """

    def __init__(self) -> None:
        super().__init__()

        self._mode: StringDescriptor = StringDescriptor(
            name='mode',
            description='Fitting strategy',
            value_spec=AttributeSpec(
                default='single',
                validator=RegexValidator(pattern=r'^(single|joint)$'),
            ),
            cif_handler=CifHandler(names=['_analysis.fit_mode']),
        )

        self._identity.category_code = 'fit_mode'

    @property
    def mode(self):
        """Active fitting strategy descriptor."""
        return self._mode

    @mode.setter
    def mode(self, value: str) -> None:
        """Set the fitting strategy value.

        Args:
            value: ``'single'`` or ``'joint'``.
        """
        self._mode.value = value
