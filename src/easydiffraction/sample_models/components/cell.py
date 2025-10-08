# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from typing import Optional

from easydiffraction.core.categories import CategoryItem
from easydiffraction.core.guards import RangeValidator
from easydiffraction.core.parameters import Parameter
from easydiffraction.crystallography.cif import CifHandler


class Cell(CategoryItem):
    def __init__(
        self,
        *,
        length_a: Optional[int | float] = None,
        length_b: Optional[int | float] = None,
        length_c: Optional[int | float] = None,
        angle_alpha: Optional[int | float] = None,
        angle_beta: Optional[int | float] = None,
        angle_gamma: Optional[int | float] = None,
    ) -> None:
        super().__init__()

        self._length_a: Parameter = Parameter(
            name='length_a',
            description='Length of the a axis of the unit cell.',
            validator=RangeValidator(ge=0, le=1000, default=10.0),
            value=length_a,
            units='Å',
            cif_handler=CifHandler(names=['_cell.length_a']),
        )
        self._length_b: Parameter = Parameter(
            name='length_b',
            description='Length of the b axis of the unit cell.',
            validator=RangeValidator(ge=0, le=1000, default=10.0),
            value=length_b,
            units='Å',
            cif_handler=CifHandler(names=['_cell.length_b']),
        )
        self._length_c: Parameter = Parameter(
            name='length_c',
            description='Length of the c axis of the unit cell.',
            validator=RangeValidator(ge=0, le=1000, default=10.0),
            value=length_c,
            units='Å',
            cif_handler=CifHandler(names=['_cell.length_c']),
        )
        self._angle_alpha: Parameter = Parameter(
            name='angle_alpha',
            description='Angle between edges b and c.',
            validator=RangeValidator(ge=0, le=180, default=90.0),
            value=angle_alpha,
            units='deg',
            cif_handler=CifHandler(names=['_cell.angle_alpha']),
        )
        self._angle_beta: Parameter = Parameter(
            name='angle_beta',
            description='Angle between edges a and c.',
            validator=RangeValidator(ge=0, le=180, default=90.0),
            value=angle_beta,
            units='deg',
            cif_handler=CifHandler(names=['_cell.angle_beta']),
        )
        self._angle_gamma: Parameter = Parameter(
            name='angle_gamma',
            description='Angle between edges a and b.',
            validator=RangeValidator(ge=0, le=180, default=90.0),
            value=angle_gamma,
            units='deg',
            cif_handler=CifHandler(names=['_cell.angle_gamma']),
        )

        self._identity.category_code = 'cell'

    @property
    def length_a(self):
        return self._length_a

    @length_a.setter
    def length_a(self, value):
        self._length_a.value = value

    @property
    def length_b(self):
        return self._length_b

    @length_b.setter
    def length_b(self, value):
        self._length_b.value = value

    @property
    def length_c(self):
        return self._length_c

    @length_c.setter
    def length_c(self, value):
        self._length_c.value = value

    @property
    def angle_alpha(self):
        return self._angle_alpha

    @angle_alpha.setter
    def angle_alpha(self, value):
        self._angle_alpha.value = value

    @property
    def angle_beta(self):
        return self._angle_beta

    @angle_beta.setter
    def angle_beta(self, value):
        self._angle_beta.value = value

    @property
    def angle_gamma(self):
        return self._angle_gamma

    @angle_gamma.setter
    def angle_gamma(self, value):
        self._angle_gamma.value = value
