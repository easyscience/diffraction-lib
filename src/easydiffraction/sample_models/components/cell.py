# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from typing import Any

from easydiffraction.core.objects import CategoryItem
from easydiffraction.core.objects import Parameter


class Cell(CategoryItem):
    """Represents the unit cell parameters of a sample model."""

    _allowed_attributes = {
        'length_a',
        'length_b',
        'length_c',
        'angle_alpha',
        'angle_beta',
        'angle_gamma',
    }

    @property
    def category_key(self) -> str:
        return 'cell'

    def __init__(
        self,
        length_a: Any = None,
        length_b: Any = None,
        length_c: Any = None,
        angle_alpha: Any = None,
        angle_beta: Any = None,
        angle_gamma: Any = None,
    ) -> None:
        super().__init__()

        self.length_a = Parameter(
            value=length_a,
            name='length_a',
            default_value=10.0,
            # physical_min=0.0,
            units='Å',
            full_cif_names=['_cell.length_a'],
            description='Length of the unit cell edge a.',
        )
        self.length_b = Parameter(
            value=length_b,
            name='length_b',
            default_value=10.0,
            # physical_min=0.0,
            units='Å',
            full_cif_names=['_cell.length_b'],
            description='Length of the unit cell edge b.',
        )
        self.length_c = Parameter(
            value=length_c,
            name='length_c',
            default_value=10.0,
            # physical_min=0.0,
            units='Å',
            full_cif_names=['_cell.length_c'],
            description='Length of the unit cell edge c.',
        )
        self.angle_alpha = Parameter(
            value=angle_alpha,
            name='angle_alpha',
            default_value=90.0,
            # physical_min=0.0,
            # physical_max=180.0,
            units='deg',
            full_cif_names=['_cell.angle_alpha'],
            description='Angle between edges b and c.',
        )
        self.angle_beta = Parameter(
            value=angle_beta,
            name='angle_beta',
            default_value=90.0,
            # physical_min=0.0,
            # physical_max=180.0,
            units='deg',
            full_cif_names=['_cell.angle_beta'],
            description='Angle between edges a and c.',
        )
        self.angle_gamma = Parameter(
            value=angle_gamma,
            name='angle_gamma',
            default_value=90.0,
            # physical_min=0.0,
            # physical_max=180.0,
            units='deg',
            full_cif_names=['_cell.angle_gamma'],
            description='Angle between edges a and b.',
        )
