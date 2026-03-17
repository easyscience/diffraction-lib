# SPDX-FileCopyrightText: 2021-2026 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
"""Unit cell parameters category for structures."""

from easydiffraction.core.category import CategoryItem
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import RangeValidator
from easydiffraction.core.variable import Parameter
from easydiffraction.crystallography import crystallography as ecr
from easydiffraction.io.cif.handler import CifHandler


class Cell(CategoryItem):
    """Unit cell with lengths *a*, *b*, *c* and angles *alpha*, *beta*,
    *gamma*.

    All six lattice parameters are exposed as :class:`Parameter`
    descriptors supporting validation, fitting and CIF serialization.
    """

    def __init__(self) -> None:
        """Initialise the unit cell with default parameter values."""
        super().__init__()

        self._length_a = Parameter(
            name='length_a',
            description='Length of the a axis of the unit cell.',
            units='Å',
            value_spec=AttributeSpec(
                default=10.0,
                validator=RangeValidator(ge=0, le=1000),
            ),
            cif_handler=CifHandler(names=['_cell.length_a']),
        )
        self._length_b = Parameter(
            name='length_b',
            description='Length of the b axis of the unit cell.',
            units='Å',
            value_spec=AttributeSpec(
                default=10.0,
                validator=RangeValidator(ge=0, le=1000),
            ),
            cif_handler=CifHandler(names=['_cell.length_b']),
        )
        self._length_c = Parameter(
            name='length_c',
            description='Length of the c axis of the unit cell.',
            units='Å',
            value_spec=AttributeSpec(
                default=10.0,
                validator=RangeValidator(ge=0, le=1000),
            ),
            cif_handler=CifHandler(names=['_cell.length_c']),
        )
        self._angle_alpha = Parameter(
            name='angle_alpha',
            description='Angle between edges b and c.',
            units='deg',
            value_spec=AttributeSpec(
                default=90.0,
                validator=RangeValidator(ge=0, le=180),
            ),
            cif_handler=CifHandler(names=['_cell.angle_alpha']),
        )
        self._angle_beta = Parameter(
            name='angle_beta',
            description='Angle between edges a and c.',
            units='deg',
            value_spec=AttributeSpec(
                default=90.0,
                validator=RangeValidator(ge=0, le=180),
            ),
            cif_handler=CifHandler(names=['_cell.angle_beta']),
        )
        self._angle_gamma = Parameter(
            name='angle_gamma',
            description='Angle between edges a and b.',
            units='deg',
            value_spec=AttributeSpec(
                default=90.0,
                validator=RangeValidator(ge=0, le=180),
            ),
            cif_handler=CifHandler(names=['_cell.angle_gamma']),
        )

        self._identity.category_code = 'cell'

    # ------------------------------------------------------------------
    #  Private helper methods
    # ------------------------------------------------------------------

    def _apply_cell_symmetry_constraints(self) -> None:
        """Apply symmetry constraints to cell parameters in place.

        Uses the parent structure's space-group symbol to determine
        which lattice parameters are dependent and sets them
        accordingly.
        """
        dummy_cell = {
            'lattice_a': self.length_a.value,
            'lattice_b': self.length_b.value,
            'lattice_c': self.length_c.value,
            'angle_alpha': self.angle_alpha.value,
            'angle_beta': self.angle_beta.value,
            'angle_gamma': self.angle_gamma.value,
        }
        space_group_name = self._parent.space_group.name_h_m.value

        ecr.apply_cell_symmetry_constraints(
            cell=dummy_cell,
            name_hm=space_group_name,
        )

        self.length_a.value = dummy_cell['lattice_a']
        self.length_b.value = dummy_cell['lattice_b']
        self.length_c.value = dummy_cell['lattice_c']
        self.angle_alpha.value = dummy_cell['angle_alpha']
        self.angle_beta.value = dummy_cell['angle_beta']
        self.angle_gamma.value = dummy_cell['angle_gamma']

    def _update(
        self,
        called_by_minimizer: bool = False,
    ) -> None:
        """Recalculate cell parameters after a change.

        Args:
            called_by_minimizer (bool): Whether the update was triggered
                by the fitting minimizer. Currently unused.
        """
        del called_by_minimizer  # TODO: ???

        self._apply_cell_symmetry_constraints()

    # ------------------------------------------------------------------
    #  Public properties
    # ------------------------------------------------------------------

    @property
    def length_a(self) -> Parameter:
        """Length of the *a* axis.

        Returns:
            Parameter: Descriptor for lattice parameter *a* (Å).
        """
        return self._length_a

    @length_a.setter
    def length_a(
        self,
        value: float,
    ) -> None:
        """Set the length of the *a* axis.

        Args:
            value (float): New length in ångströms.
        """
        self._length_a.value = value

    @property
    def length_b(self) -> Parameter:
        """Length of the *b* axis.

        Returns:
            Parameter: Descriptor for lattice parameter *b* (Å).
        """
        return self._length_b

    @length_b.setter
    def length_b(
        self,
        value: float,
    ) -> None:
        """Set the length of the *b* axis.

        Args:
            value (float): New length in ångströms.
        """
        self._length_b.value = value

    @property
    def length_c(self) -> Parameter:
        """Length of the *c* axis.

        Returns:
            Parameter: Descriptor for lattice parameter *c* (Å).
        """
        return self._length_c

    @length_c.setter
    def length_c(
        self,
        value: float,
    ) -> None:
        """Set the length of the *c* axis.

        Args:
            value (float): New length in ångströms.
        """
        self._length_c.value = value

    @property
    def angle_alpha(self) -> Parameter:
        """Angle between edges *b* and *c*.

        Returns:
            Parameter: Descriptor for angle *α* (degrees).
        """
        return self._angle_alpha

    @angle_alpha.setter
    def angle_alpha(
        self,
        value: float,
    ) -> None:
        """Set the angle between edges *b* and *c*.

        Args:
            value (float): New angle in degrees.
        """
        self._angle_alpha.value = value

    @property
    def angle_beta(self) -> Parameter:
        """Angle between edges *a* and *c*.

        Returns:
            Parameter: Descriptor for angle *β* (degrees).
        """
        return self._angle_beta

    @angle_beta.setter
    def angle_beta(
        self,
        value: float,
    ) -> None:
        """Set the angle between edges *a* and *c*.

        Args:
            value (float): New angle in degrees.
        """
        self._angle_beta.value = value

    @property
    def angle_gamma(self) -> Parameter:
        """Angle between edges *a* and *b*.

        Returns:
            Parameter: Descriptor for angle *γ* (degrees).
        """
        return self._angle_gamma

    @angle_gamma.setter
    def angle_gamma(
        self,
        value: float,
    ) -> None:
        """Set the angle between edges *a* and *b*.

        Args:
            value (float): New angle in degrees.
        """
        self._angle_gamma.value = value
