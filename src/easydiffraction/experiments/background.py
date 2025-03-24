import numpy as np
from scipy.interpolate import interp1d

from easydiffraction.utils.utils import paragraph


class Background:
    """Base background class."""

    def __init__(self):
        self.points = []


class PointBackground(Background):
    def __init__(self):
        super().__init__()

    def add(self, x, y):
        """Add a background point."""
        self.points.append((x, y))

    def interpolate(self, x_data):
        """Interpolate background points over x_data."""
        if not self.points:
            print('Warning: No background points found. Setting background to zero.')
            return np.zeros_like(x_data)

        background_points = np.array(self.points)
        bg_x, bg_y = background_points[:, 0], background_points[:, 1]

        interp_func = interp1d(
            bg_x, bg_y,
            kind='linear',
            bounds_error=False,
            fill_value=(bg_y[0], bg_y[-1])
        )
        return interp_func(x_data)

    def show(self):
        print(paragraph("Background points"))
        for point in self.points:
            print(f"({point[0]}, {point[1]})")


class PolynomialBackground(Background):
    def __init__(self):
        super().__init__()
        self.coefficients = [1.0, 0.0]  # Placeholder coefficients


class BackgroundFactory:
    @staticmethod
    def create_background(background_type):
        if background_type == "point":
            return PointBackground()
        elif background_type == "polynomial":
            return PolynomialBackground()
        else:
            raise ValueError(f"Unknown background type: {background_type}")