import numpy as np

from easydiffraction.analysis.reliability_factors import calculate_reduced_chi_square

SIGNIFICANT_CHANGE_THRESHOLD = 0.01  # 1% threshold
FIXED_WIDTH = 17

def format_cell(cell, width=FIXED_WIDTH, align="center"):
    cell_str = str(cell)
    if align == "center":
        return cell_str.center(width)
    elif align == "left":
        return cell_str.ljust(width)
    elif align == "right":
        return cell_str.rjust(width)
    else:
        return cell_str


class FittingProgressTracker:
    """
    Tracks and reports the reduced chi-square during the optimization process.
    """

    def __init__(self):
        self._iteration = 0
        self._previous_chi2 = None
        self._last_chi2 = None
        self._last_iteration = None
        self._best_chi2 = None
        self._best_iteration = None
        self._fitting_time = None

    def reset(self):
        self._iteration = 0
        self._previous_chi2 = None
        self._last_chi2 = None
        self._last_iteration = None
        self._best_chi2 = None
        self._best_iteration = None
        self._fitting_time = None

    def track(self, residuals, parameters):
        """
        Track chi-square progress during the optimization process.

        Parameters:
            residuals (np.ndarray): Array of residuals between measured and calculated data.
            parameters (list): List of free parameters being fitted.

        Returns:
            np.ndarray: Residuals unchanged, for optimizer consumption.
        """
        self._iteration += 1

        reduced_chi2 = calculate_reduced_chi_square(residuals, len(parameters))

        row = []

        # First iteration, initialize tracking
        if self._previous_chi2 is None:
            self._previous_chi2 = reduced_chi2
            self._best_chi2 = reduced_chi2
            self._best_iteration = self._iteration

            row = [
                self._iteration,
                f"{reduced_chi2:.2f}",
                "",
                ""
            ]

        # Improvement check
        elif (self._previous_chi2 - reduced_chi2) / self._previous_chi2 > SIGNIFICANT_CHANGE_THRESHOLD:
            change_percent = (self._previous_chi2 - reduced_chi2) / self._previous_chi2 * 100

            row = [
                self._iteration,
                f"{self._previous_chi2:.2f}",
                f"{reduced_chi2:.2f}",
                f"{change_percent:.1f}% ↓"
            ]

            self._previous_chi2 = reduced_chi2

        # Output if there is something new to display
        if row:
            self.add_tracking_info(row)

        # Update best chi-square if better
        if reduced_chi2 < self._best_chi2:
            self._best_chi2 = reduced_chi2
            self._best_iteration = self._iteration

        # Store last chi-square and iteration
        self._last_chi2 = reduced_chi2
        self._last_iteration = self._iteration

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

    @property
    def fitting_time(self):
        return self._fitting_time

    def start_timer(self):
        import time
        self._start_time = time.perf_counter()

    def stop_timer(self):
        import time
        self._end_time = time.perf_counter()
        self._fitting_time = self._end_time - self._start_time

    def start_tracking(self, minimizer_name):
        headers = ["iteration", "start", "improved", "improvement [%]"]

        print(f"🚀 Starting fitting process with '{minimizer_name}'...")
        print("📈 Goodness-of-fit (reduced χ²) change:")

        # Top border
        print("╒" + "╤".join(["═" * FIXED_WIDTH for _ in headers]) + "╕")

        # Header row (all centered)
        header_row = "│" + "│".join([format_cell(h, align="center") for h in headers]) + "│"
        print(header_row)

        # Separator
        print("╞" + "╪".join(["═" * FIXED_WIDTH for _ in headers]) + "╡")

    def add_tracking_info(self, row):
        # Alignments for each column: iteration, start, improved, change [%]
        aligns = ["center", "center", "center", "center"]

        formatted_row = "│" + "│".join([
            format_cell(cell, align=aligns[i])
            for i, cell in enumerate(row)
        ]) + "│"

        print(formatted_row)

    def finish_tracking(self):
        # Print last iteration as last row
        row = [
            self._last_iteration,
            "",
            f"{self._last_chi2:.2f}",
            ""
        ]
        self.add_tracking_info(row)

        # Print bottom border
        print("╘" + "╧".join(["═" * FIXED_WIDTH for _ in range(4)]) + "╛")

        # Print best result
        print(f"🏆 Best goodness-of-fit (reduced χ²) is {self._best_chi2:.2f} at iteration {self._best_iteration}")
        print("✅ Fitting complete.")