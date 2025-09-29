# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from abc import abstractmethod
from enum import Enum
from typing import Dict
from typing import List
from typing import Optional
from typing import Type
from typing import Union

import numpy as np
from numpy.polynomial.chebyshev import chebval
from scipy.interpolate import interp1d

from easydiffraction.core.categories import CategoryCollection
from easydiffraction.core.categories import CategoryItem
from easydiffraction.core.parameters import Descriptor
from easydiffraction.core.parameters import Parameter
from easydiffraction.utils.formatting import paragraph
from easydiffraction.utils.formatting import warning
from easydiffraction.utils.utils import render_table


# TODO: rename to LineSegment
class Point(CategoryItem):
    _class_public_attrs = {
        'name',
        'x',
        'y',
    }

    @property
    def category_key(self) -> str:
        return 'background'

    def __init__(
        self,
        x: float,
        y: float,
    ):
        super().__init__()

        self.x = Descriptor(
            value=x,
            name='x',
            value_type=float,
            full_cif_names=['_pd_background.line_segment_X'],
            default_value=x,
            description='X-coordinates used to create many straight-line segments '
            'representing the background in a calculated diffractogram.',
        )
        self.y = Parameter(
            value=y,  # TODO: rename to intensity
            name='y',  # TODO: rename to intensity
            full_cif_names=['_pd_background.line_segment_intensity'],
            default_value=y,
            description='Intensity used to create many straight-line segments '
            'representing the background in a calculated diffractogram',
        )
        # self._category_entry_attr_name = str(x)
        self._category_entry_attr_name = self.x.name
        self.name = self.x.value


class PolynomialTerm(CategoryItem):
    """Chebyshev polynomial term.

    New public attribute names: ``order`` and ``coef`` replacing the
    longer ``chebyshev_order`` / ``chebyshev_coef``. Backward-compatible
    aliases are kept so existing serialized data / external code does
    not break immediately. Tests should migrate to the short names.
    """

    _class_public_attrs = {
        # New canonical names
        'order',
        'coef',
        # Backward compatibility (aliases)
        'chebyshev_order',
        'chebyshev_coef',
    }

    @property
    def category_key(self) -> str:  # noqa: D401
        return 'background'

    def __init__(self, order: int, coef: float) -> None:
        super().__init__()

        # Canonical descriptors
        self.order = Descriptor(
            value=order,
            name='order',
            value_type=int,
            full_cif_names=['_pd_background.Chebyshev_order'],
            default_value=order,
            description='Order used in a Chebyshev polynomial background term',
        )
        self.coef = Parameter(
            value=coef,
            name='coef',
            full_cif_names=['_pd_background.Chebyshev_coef'],
            default_value=coef,
            description='Coefficient used in a Chebyshev polynomial background term',
        )

        # Backward-compatible aliases (point to same objects)
        self.chebyshev_order = self.order
        self.chebyshev_coef = self.coef

        # Entry attribute used as the identifier within the collection
        self._category_entry_attr_name = self.order.name


class BackgroundBase(CategoryCollection):
    @abstractmethod
    def calculate(self, x_data: np.ndarray) -> np.ndarray:
        pass

    @abstractmethod
    def show(self) -> None:
        pass


class LineSegmentBackground(BackgroundBase):
    _description: str = 'Linear interpolation between points'

    def __init__(self):
        super().__init__(item_type=Point)

    def calculate(self, x_data: np.ndarray) -> np.ndarray:
        """Interpolate background points over x_data."""
        if not self:
            print(warning('No background points found. Setting background to zero.'))
            return np.zeros_like(x_data)

        background_x = np.array([point.x.value for point in self.values()])
        background_y = np.array([point.y.value for point in self.values()])
        interp_func = interp1d(
            background_x,
            background_y,
            kind='linear',
            bounds_error=False,
            fill_value=(
                background_y[0],
                background_y[-1],
            ),
        )
        y_data = interp_func(x_data)
        return y_data

    def show(self) -> None:
        columns_headers: List[str] = ['X', 'Intensity']
        columns_alignment = ['left', 'left']
        columns_data: List[List[float]] = []
        for point in self._items.values():
            x = point.x.value
            y = point.y.value
            columns_data.append([x, y])

        print(paragraph('Line-segment background points'))
        render_table(
            columns_headers=columns_headers,
            columns_alignment=columns_alignment,
            columns_data=columns_data,
        )


class ChebyshevPolynomialBackground(BackgroundBase):
    _description: str = 'Chebyshev polynomial background'

    def __init__(self):
        super().__init__(item_type=PolynomialTerm)

    def calculate(self, x_data: np.ndarray) -> np.ndarray:
        """Evaluate polynomial background over x_data."""
        if not self._items:
            print(warning('No background points found. Setting background to zero.'))
            return np.zeros_like(x_data)

        u = (x_data - x_data.min()) / (x_data.max() - x_data.min()) * 2 - 1  # scale to [-1, 1]
        coefs = [term.chebyshev_coef.value for term in self._items.values()]
        y_data = chebval(u, coefs)
        return y_data

    def show(self) -> None:
        columns_headers: List[str] = ['Order', 'Coefficient']
        columns_alignment = ['left', 'left']
        columns_data: List[List[Union[int, float]]] = []
        for term in self._items.values():
            order = term.chebyshev_order.value
            coef = term.chebyshev_coef.value
            columns_data.append([order, coef])

        print(paragraph('Chebyshev polynomial background terms'))
        render_table(
            columns_headers=columns_headers,
            columns_alignment=columns_alignment,
            columns_data=columns_data,
        )


class BackgroundTypeEnum(str, Enum):
    LINE_SEGMENT = 'line-segment'
    CHEBYSHEV = 'chebyshev polynomial'

    @classmethod
    def default(cls) -> 'BackgroundTypeEnum':
        return cls.LINE_SEGMENT

    def description(self) -> str:
        if self is BackgroundTypeEnum.LINE_SEGMENT:
            return 'Linear interpolation between points'
        elif self is BackgroundTypeEnum.CHEBYSHEV:
            return 'Chebyshev polynomial background'


class BackgroundFactory:
    BT = BackgroundTypeEnum
    _supported: Dict[BT, Type[BackgroundBase]] = {
        BT.LINE_SEGMENT: LineSegmentBackground,
        BT.CHEBYSHEV: ChebyshevPolynomialBackground,
    }

    @classmethod
    def create(
        cls,
        background_type: Optional[BackgroundTypeEnum] = None,
    ) -> BackgroundBase:
        if background_type is None:
            background_type = BackgroundTypeEnum.default()

        if background_type not in cls._supported:
            supported_types = list(cls._supported.keys())

            raise ValueError(
                f"Unsupported background type: '{background_type}'.\n"
                f' Supported background types: {[bt.value for bt in supported_types]}'
            )

        background_class = cls._supported[background_type]
        return background_class()
