import numpy as np


class ChiSquareTracker:
    """
    Tracks and reports the reduced chi-square during the optimization process.
    """

    def __init__(self):
        self._iteration = 0
        self._previous_chi2 = None
        self._best_chi2 = None
        self._best_iteration = None

    def reset(self):
        self._iteration = 0
        self._previous_chi2 = None
        self._best_chi2 = None
        self._best_iteration = None

    def track(self, residuals, parameters):
        """
        Track chi-square progress during the optimization process.

        Parameters:
            residuals (np.ndarray): Array of residuals between measured and calculated data.
            parameters (list): List of free parameters being refined.

        Returns:
            np.ndarray: Residuals unchanged, for optimizer consumption.
        """
        self._iteration += 1

        chi2 = np.sum(residuals ** 2)
        n_points = len(residuals)
        n_parameters = len(parameters)

        red_chi2 = chi2 / max((n_points - n_parameters), 1)

        row = []

        # First iteration, initialize tracking
        if self._previous_chi2 is None:
            self._previous_chi2 = red_chi2
            self._best_chi2 = red_chi2
            self._best_iteration = self._iteration

            row = [
                self._iteration,
                f"{red_chi2:<12.2f}",
                "-".ljust(12),
                "-".ljust(12)
            ]

        # Improvement check
        elif (self._previous_chi2 - red_chi2) / self._previous_chi2 > 0.01:
            change_percent = (self._previous_chi2 - red_chi2) / self._previous_chi2 * 100

            row = [
                self._iteration,
                f"{self._previous_chi2:<12.2f}",
                f"{red_chi2:<12.2f}",
                f"↓ {change_percent:.1f}%".ljust(10)
            ]

            self._previous_chi2 = red_chi2

        # Output if there is something new to display
        if row:
            print(f"| {row[0]:<11} | {row[1]:<12} | {row[2]:<12} | {row[3]:<12} |")

        # Update best chi-square if better
        if self._best_chi2 is None or red_chi2 < self._best_chi2:
            self._best_chi2 = red_chi2
            self._best_iteration = self._iteration

        return residuals

    @property
    def best_chi2(self):
        return self._best_chi2

    @property
    def best_iteration(self):
        return self._best_iteration

    @property
    def iteration(self):
        return self._iteration

    def start_tracking(self, minimizer_name):
        print("🚀 Starting fitting process with {}...".format(minimizer_name))
        print("📈 Reduced Chi-square change:")
        print("+-------------+--------------+--------------+--------------+")
        print(f"| {'iteration':<11} | {'start':<12} | {'improved':<12} | {'change [%]':<12} |")
        print("+=============+==============+==============+==============+")

    def finish_tracking(self, fitting_time):
        print("+-------------+--------------+--------------+--------------+")
        final_chi2 = self._previous_chi2 if self._previous_chi2 is not None else (self._best_chi2 if self._best_chi2 is not None else 0.0)
        final_iteration = self._iteration if self._iteration is not None else "N/A"
        best_chi2_str = f"{self._best_chi2:.2f}" if self._best_chi2 is not None else "N/A"

        print(f"🔧 Final iteration {final_iteration}: Reduced Chi-square = {final_chi2:.2f}")
        print(f"🏆 Best Reduced Chi-square: {best_chi2_str} at iteration {self._best_iteration if self._best_iteration is not None else 'N/A'}")
        print(f"⏱️ Fitting time: {fitting_time:.2f} seconds")
        print("✅ Fitting complete.")