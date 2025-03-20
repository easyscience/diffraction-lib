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