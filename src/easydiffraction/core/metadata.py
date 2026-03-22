# SPDX-FileCopyrightText: 2021-2026 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
"""Metadata dataclasses for factory-created classes.

Three frozen dataclasses describe a concrete class:

- ``TypeInfo`` — stable tag and human-readable description.
- ``Compatibility`` — experimental conditions (multiple fields).
- ``CalculatorSupport`` — which calculation engines can handle it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import FrozenSet


@dataclass(frozen=True)
class TypeInfo:
    """Stable identity and human-readable description for a factory-
    created class.

    Attributes:
        tag: Short, stable string identifier used for serialization,
            user-facing selection, and factory lookup.  Must be unique
            within a factory's registry.  Examples: ``'line-segment'``,
            ``'pseudo-voigt'``, ``'cryspy'``.
        description: One-line human-readable explanation.  Used in
            ``show_supported()`` tables and documentation.
    """

    tag: str
    description: str = ''


@dataclass(frozen=True)
class Compatibility:
    """Experimental conditions under which a class can be used.

    Each field is a frozenset of enum values representing the set of
    supported values for that axis.  An empty frozenset means
    "compatible with any value of this axis" (i.e. no restriction).
    """

    sample_form: FrozenSet = frozenset()
    scattering_type: FrozenSet = frozenset()
    beam_mode: FrozenSet = frozenset()
    radiation_probe: FrozenSet = frozenset()

    def supports(
        self,
        sample_form=None,
        scattering_type=None,
        beam_mode=None,
        radiation_probe=None,
    ) -> bool:
        """Check if this compatibility matches the given conditions.

        Each argument is an optional enum member.  Returns ``True`` if
        every provided value is in the corresponding frozenset (or the
        frozenset is empty, meaning *any*).

        Example::

            compat.supports(
                scattering_type=ScatteringTypeEnum.BRAGG,
                beam_mode=BeamModeEnum.CONSTANT_WAVELENGTH,
            )
        """
        for axis, value in (
            ('sample_form', sample_form),
            ('scattering_type', scattering_type),
            ('beam_mode', beam_mode),
            ('radiation_probe', radiation_probe),
        ):
            if value is None:
                continue
            allowed = getattr(self, axis)
            if allowed and value not in allowed:
                return False
        return True


@dataclass(frozen=True)
class CalculatorSupport:
    """Which calculation engines can handle this class.

    Attributes:
        calculators: Frozenset of ``CalculatorEnum`` values.  Empty
            means "any calculator" (no restriction).
    """

    calculators: FrozenSet = frozenset()

    def supports(self, calculator) -> bool:
        """Check if a specific calculator can handle this class.

        Args:
            calculator: A ``CalculatorEnum`` value.

        Returns:
            ``True`` if the calculator is in the set, or if the set is
            empty (meaning any calculator is accepted).
        """
        if not self.calculators:
            return True
        return calculator in self.calculators
