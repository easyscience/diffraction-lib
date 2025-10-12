# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from abc import abstractmethod
from enum import Enum
from typing import Any
from typing import Optional

from easydiffraction.core.categories import CategoryCollection
from easydiffraction.core.categories import CategoryItem
from easydiffraction.core.parameters import DescriptorFloat
from easydiffraction.core.parameters import Parameter
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import DataTypes
from easydiffraction.core.validation import RangeValidator
from easydiffraction.io.cif.handler import CifHandler


# TODO: rename to LineSegment
class Point(CategoryItem):
    def __init__(self, *, x: float, y: float):
        super().__init__()

        self._x = DescriptorFloat(
            name='x',
            description=(
                'X-coordinates used to create many straight-line segments '
                'representing the background in a calculated diffractogram.'
            ),
            value_spec=AttributeSpec(
                value=x,
                type_=DataTypes.NUMERIC,
                default=0.0,
                content_validator=RangeValidator(),
            ),
            cif_handler=CifHandler(names=['_pd_background.line_segment_X']),
        )
        self._y = Parameter(
            name='y',  # TODO: rename to intensity
            description=(
                'Intensity used to create many straight-line segments '
                'representing the background in a calculated diffractogram'
            ),
            value_spec=AttributeSpec(
                value=y,
                type_=DataTypes.NUMERIC,
                default=0.0,
                content_validator=RangeValidator(),
            ),  # TODO: rename to intensity
            cif_handler=CifHandler(names=['_pd_background.line_segment_intensity']),
        )

        self._identity.category_code = 'background'
        self._identity.category_entry_name = lambda: str(self.x.value)

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, value):
        self._x.value = value

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, value):
        self._y.value = value


class PolynomialTerm(CategoryItem):
    """Chebyshev polynomial term.

    New public attribute names: ``order`` and ``coef`` replacing the
    longer ``chebyshev_order`` / ``chebyshev_coef``. Backward-compatible
    aliases are kept so existing serialized data / external code does
    not break immediately. Tests should migrate to the short names.
    """

    def __init__(self, *, order: int, coef: float) -> None:
        super().__init__()

        # Canonical descriptors
        self._order = DescriptorFloat(
            name='order',
            description='Order used in a Chebyshev polynomial background term',
            value_spec=AttributeSpec(
                value=order,
                type_=DataTypes.NUMERIC,
                default=0.0,
                content_validator=RangeValidator(),
            ),
            cif_handler=CifHandler(names=['_pd_background.Chebyshev_order']),
        )
        self._coef = Parameter(
            name='coef',
            description='Coefficient used in a Chebyshev polynomial background term',
            value_spec=AttributeSpec(
                value=coef,
                type_=DataTypes.NUMERIC,
                default=0.0,
                content_validator=RangeValidator(),
            ),
            cif_handler=CifHandler(names=['_pd_background.Chebyshev_coef']),
        )

        self._identity.category_code = 'background'
        self._identity.category_entry_name = lambda: str(self.order.value)

    @property
    def order(self):
        return self._order

    @order.setter
    def order(self, value):
        self._order.value = value

    @property
    def coef(self):
        return self._coef

    @coef.setter
    def coef(self, value):
        self._coef.value = value


class BackgroundBase(CategoryCollection):
    @abstractmethod
    def calculate(self, x_data: Any) -> Any:
        pass

    @abstractmethod
    def show(self) -> None:
        pass


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

    @classmethod
    def _supported_map(cls) -> dict:
        # Lazy import to avoid circulars
        from easydiffraction.experiments.category_collections.background_types.chebyshev import (
            ChebyshevPolynomialBackground,
        )
        from easydiffraction.experiments.category_collections.background_types.line_segment import (
            LineSegmentBackground,
        )

        return {
            cls.BT.LINE_SEGMENT: LineSegmentBackground,
            cls.BT.CHEBYSHEV: ChebyshevPolynomialBackground,
        }

    @classmethod
    def create(
        cls,
        background_type: Optional[BackgroundTypeEnum] = None,
    ) -> BackgroundBase:
        if background_type is None:
            background_type = BackgroundTypeEnum.default()

        supported = cls._supported_map()
        if background_type not in supported:
            supported_types = list(supported.keys())

            raise ValueError(
                f"Unsupported background type: '{background_type}'.\n"
                f' Supported background types: {[bt.value for bt in supported_types]}'
            )

        background_class = supported[background_type]
        return background_class()
