class Background:
    """Base background class."""

    def __init__(self):
        self.points = []


class PointBackground(Background):
    def __init__(self):
        super().__init__()
        self.points = [(2000.0, 221.1), (4000.0, 169.5), (6000.0, 135.4)]  # Example points


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