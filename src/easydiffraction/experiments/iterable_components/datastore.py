import numpy as np


class Pattern:
    """
    Base pattern class for both powder and single crystal experiments.
    Stores x, measured intensities, uncertainties, background, and calculated intensities.
    """

    def __init__(self, experiment):
        self.experiment = experiment

        # Data arrays
        self.x = None
        self.meas = None
        self.meas_su = None
        self.bkg = None
        self._calc = None  # Cached calculated intensities

    @property
    def calc(self):
        """Access calculated intensities. Should be updated via external calculation."""
        return self._calc

    @calc.setter
    def calc(self, values):
        """Set calculated intensities (from Analysis.calculate_pattern())."""
        self._calc = values


class PowderPattern(Pattern):
    """
    Specialized pattern for powder diffraction (can be extended in the future).
    """
    def __init__(self, experiment):
        super().__init__(experiment)
        # Additional powder-specific initialization if needed


class Datastore:
    """
    Stores pattern data (measured and calculated) for an experiment.
    """

    def __init__(self, sample_form: str, experiment):
        self.sample_form = sample_form

        if sample_form == "powder":
            self.pattern = PowderPattern(experiment)
        elif sample_form == "single_crystal":
            self.pattern = Pattern(experiment)
        else:
            raise ValueError(f"Unknown sample form '{sample_form}'")

    def load_measured_data(self, file_path):
        """Load measured data from an ASCII file."""
        print(f"Loading measured data for {self.sample_form} diffraction from {file_path}")

        try:
            data = np.loadtxt(file_path)
        except Exception as e:
            print(f"Failed to load data: {e}")
            return

        if data.shape[1] < 2:
            raise ValueError("Data file must have at least two columns (x and y).")

        x = data[:, 0]
        y = data[:, 1]
        sy = data[:, 2] if data.shape[1] > 2 else np.sqrt(np.abs(y))

        self.pattern.x = x
        self.pattern.meas = y
        self.pattern.meas_su = sy

        print(f"Loaded {len(x)} points for experiment '{self.pattern.experiment.name}'.")

    def show_measured_data(self):
        """Display measured data in console."""
        print(f"\nMeasured data ({self.sample_form}):")
        print(f"x: {self.pattern.x}")
        print(f"meas: {self.pattern.meas}")
        print(f"meas_su: {self.pattern.meas_su}")

    def show_calculated_data(self):
        """Display calculated data in console."""
        print(f"\nCalculated data ({self.sample_form}):")
        print(f"calc: {self.pattern.calc}")


class DatastoreFactory:
    """
    Factory to dynamically create appropriate datastore instances (SC/Powder).
    """

    @staticmethod
    def create(sample_form: str, experiment):
        """
        Create a datastore object depending on the sample form.
        """
        return Datastore(sample_form, experiment)