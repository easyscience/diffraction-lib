# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Unit cell parameters category for structures."""

from __future__ import annotations

from easydiffraction.core.category import CategoryItem
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import RangeValidator
from easydiffraction.core.variable import Parameter
from easydiffraction.crystallography import crystallography as ecr
from easydiffraction.datablocks.structure.categories.cell.factory import CellFactory
from easydiffraction.io.cif.handler import CifHandler


@CellFactory.register
class Cell(CategoryItem):
    """
    Unit cell with lengths a, b, c and angles alpha, beta, gamma.

    All six lattice parameters are exposed as :class:`Parameter`
    descriptors supporting validation, fitting and CIF serialization.
    """

    type_info = TypeInfo(
        tag='default',
        description='Unit cell parameters',
    )

    def __init__(self) -> None:
        """Initialise the unit cell with default parameter values."""
        super().__init__()

        self._length_a = Parameter(
            name='length_a',
            description='Length of the a axis of the unit cell',
            units='Å',
            value_spec=AttributeSpec(
                default=10.0,
                validator=RangeValidator(ge=0, le=30),
            ),
            cif_handler=CifHandler(names=['_cell.length_a']),
        )
        self._length_b = Parameter(
            name='length_b',
            description='Length of the b axis of the unit cell',
            units='Å',
            value_spec=AttributeSpec(
                default=10.0,
                validator=RangeValidator(ge=0, le=30),
            ),
            cif_handler=CifHandler(names=['_cell.length_b']),
        )
        self._length_c = Parameter(
            name='length_c',
            description='Length of the c axis of the unit cell',
            units='Å',
            value_spec=AttributeSpec(
                default=10.0,
                validator=RangeValidator(ge=0, le=30),
            ),
            cif_handler=CifHandler(names=['_cell.length_c']),
        )
        self._angle_alpha = Parameter(
            name='angle_alpha',
            description='Angle between edges b and c',
            units='deg',
            value_spec=AttributeSpec(
                default=90.0,
                validator=RangeValidator(ge=0, le=180),
            ),
            cif_handler=CifHandler(names=['_cell.angle_alpha']),
        )
        self._angle_beta = Parameter(
            name='angle_beta',
            description='Angle between edges a and c',
            units='deg',
            value_spec=AttributeSpec(
                default=90.0,
                validator=RangeValidator(ge=0, le=180),
            ),
            cif_handler=CifHandler(names=['_cell.angle_beta']),
        )
        self._angle_gamma = Parameter(
            name='angle_gamma',
            description='Angle between edges a and b',
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
        """
        Apply symmetry constraints to cell parameters in place.

        Uses the parent structure's space-group symbol to determine
        which lattice parameters are dependent and sets them
        accordingly. Dependent parameters are also flagged as
        ``symmetry_fixed`` so they cannot be marked refinable.
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
        fixed_flags = ecr.cell_symmetry_fixed_flags(name_hm=space_group_name)

        param_by_key = {
            'lattice_a': self._length_a,
            'lattice_b': self._length_b,
            'lattice_c': self._length_c,
            'angle_alpha': self._angle_alpha,
            'angle_beta': self._angle_beta,
            'angle_gamma': self._angle_gamma,
        }
        for key, param in param_by_key.items():
            param.value = dummy_cell[key]
            param._set_symmetry_fixed(value=fixed_flags[key])

    def _update(
        self,
        *,
        called_by_minimizer: bool = False,
    ) -> None:
        """
        Recalculate cell parameters after a change.

        Parameters
        ----------
        called_by_minimizer : bool, default=False
            Whether the update was triggered by the fitting minimizer.
            Currently unused.
        """
        del called_by_minimizer  # TODO: ???

        self._apply_cell_symmetry_constraints()

    # ------------------------------------------------------------------
    #  Public properties
    # ------------------------------------------------------------------

    @property
    def length_a(self) -> Parameter:
        """
        Length of the a axis of the unit cell (Å).

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._length_a

    @length_a.setter
    def length_a(self, value: float) -> None:
        self._length_a.value = value

    @property
    def length_b(self) -> Parameter:
        """
        Length of the b axis of the unit cell (Å).

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._length_b

    @length_b.setter
    def length_b(self, value: float) -> None:
        self._length_b.value = value

    @property
    def length_c(self) -> Parameter:
        """
        Length of the c axis of the unit cell (Å).

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._length_c

    @length_c.setter
    def length_c(self, value: float) -> None:
        self._length_c.value = value

    @property
    def angle_alpha(self) -> Parameter:
        """
        Angle between edges b and c (deg).

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._angle_alpha

    @angle_alpha.setter
    def angle_alpha(self, value: float) -> None:
        self._angle_alpha.value = value

    @property
    def angle_beta(self) -> Parameter:
        """
        Angle between edges a and c (deg).

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._angle_beta

    @angle_beta.setter
    def angle_beta(self, value: float) -> None:
        self._angle_beta.value = value

    @property
    def angle_gamma(self) -> Parameter:
        """
        Angle between edges a and b (deg).

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._angle_gamma

    @angle_gamma.setter
    def angle_gamma(self, value: float) -> None:
        self._angle_gamma.value = value
