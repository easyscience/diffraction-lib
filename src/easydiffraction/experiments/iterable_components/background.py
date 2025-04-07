import numpy as np
import tabulate

from abc import ABC, abstractmethod
from numpy.polynomial.chebyshev import chebval
from scipy.interpolate import interp1d

from easydiffraction.utils.formatting import (paragraph,
                                              warning)
from easydiffraction.core.parameter import (Parameter,
                                            Descriptor)
from easydiffraction.core.component import (IterableComponent,
                                            IterableComponentRow)
from easydiffraction.core.constants import DEFAULT_BACKGROUND_TYPE


class Point(IterableComponentRow):
    def __init__(self, x: float, y: float):
        super().__init__()

        self.x = Descriptor(
            value=x,
            cif_name='line_segment_X',
            description="X-coordinates used to create many straight-line segments representing the background in a calculated diffractogram."
        )
        self.y = Parameter(
            value=y,
            cif_name='line_segment_intensity',
            description="Intensity used to create many straight-line segments representing the background in a calculated diffractogram"
        )

        self._locked = True  # Lock further attribute additions

    # TODO: Temporary workaround for getting str type for id.value
    # TODO: Switch to str type for id?
    @property
    def id(self):
        return Descriptor(f"{self.x.value}", cif_name="blablabla")


class PolynomialTerm(IterableComponentRow):
    def __init__(self, order, coef):
        super().__init__()

        self.order = Descriptor(
            value=order,
            cif_name='Chebyshev_order',
            description="The value of an order used in a Chebyshev polynomial equation representing the background in a calculated diffractogram"
        )
        self.coef = Parameter(
            value=coef,
            cif_name='Chebyshev_coef',
            description="The value of a coefficient used in a Chebyshev polynomial equation representing the background in a calculated diffractogram"
        )

        self._locked = True  # Lock further attribute additions

    # TODO: Temporary workaround for getting str type for id.value
    # TODO: Switch to str type for id?
    @property
    def id(self):
        return Descriptor(f"{self.order.value}", cif_name="blablabla")


class BackgroundBase(IterableComponent):
    @property
    def cif_category_name(self):
        return "_pd_background"

    @abstractmethod
    def add(self, *args):
        pass

    @abstractmethod
    def calculate(self, x_data):
        pass

    @abstractmethod
    def show(self):
        pass


class LineSegmentBackground(BackgroundBase):
    _description = 'Linear interpolation between points'

    def __init__(self):
        super().__init__()

    def add(self, x, y):
        """Add a background point."""
        point = Point(x=x, y=y)
        self._rows.append(point)

    def calculate(self, x_data):
        """Interpolate background points over x_data."""
        if not self._rows:
            print(warning('No background points found. Setting background to zero.'))
            return np.zeros_like(x_data)

        background_x = np.array([point.x.value for point in self._rows])
        background_y = np.array([point.y.value for point in self._rows])
        interp_func = interp1d(
            background_x, background_y,
            kind='linear',
            bounds_error=False,
            fill_value=(background_y[0], background_y[-1])
        )
        y_data = interp_func(x_data)
        return y_data

    def show(self):
        header = ["X", "Intensity"]
        table_data = []

        for point in self._rows:
            x = point.x.value
            y = point.y.value
            table_data.append([x, y])

        print(paragraph("Line-segment background points"))
        print(tabulate.tabulate(
            table_data,
            headers=header,
            tablefmt="fancy_outline",
            numalign="left",
            stralign="left",
            showindex=False
        ))


class ChebyshevPolynomialBackground(BackgroundBase):
    _description = 'Chebyshev polynomial background'

    def __init__(self):
        super().__init__()

    def add(self, order, coef):
        """Add a polynomial term as (order, coefficient)."""
        term = PolynomialTerm(order=order, coef=coef)
        self._rows.append(term)

    def calculate(self, x_data):
        """Evaluate polynomial background over x_data."""
        if not self._rows:
            print(warning('No background points found. Setting background to zero.'))
            return np.zeros_like(x_data)

        u = (x_data - x_data.min()) / (x_data.max() - x_data.min()) * 2 - 1  # scale to [-1, 1]
        coefs = [term.coef.value for term in self._rows]
        y_data = chebval(u, coefs)
        return y_data

    def show(self):
        header = ["Order", "Coefficient"]
        table_data = []

        for term in self._rows:
            order = term.order.value
            coef = term.coef.value
            table_data.append([order, coef])

        print(paragraph("Chebyshev polynomial background terms"))
        print(tabulate.tabulate(
            table_data,
            headers=header,
            tablefmt="fancy_outline",
            numalign="left",
            stralign="left",
            showindex=False
        ))


class BackgroundFactory:
    _supported = {
        "line-segment": LineSegmentBackground,
        "chebyshev polynomial": ChebyshevPolynomialBackground
    }

    @classmethod
    def create(cls,
               background_type=DEFAULT_BACKGROUND_TYPE):
        if background_type not in cls._supported:
            supported_types = list(cls._supported.keys())

            raise ValueError(
                f"Unsupported background type: '{background_type}'.\n "
                f"Supported background types: {supported_types}"
            )

        background_class = cls._supported[background_type]
        return background_class()
