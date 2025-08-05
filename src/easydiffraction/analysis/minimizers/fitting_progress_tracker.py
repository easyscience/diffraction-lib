import numpy as np
import time
from typing import List, Optional

try:
    from IPython.display import (
        display,
        clear_output
    )
except ImportError:
    display = None
    clear_output = None

from easydiffraction.utils.utils import (
    is_notebook,
    render_table
)
from easydiffraction.analysis.reliability_factors import calculate_reduced_chi_square

SIGNIFICANT_CHANGE_THRESHOLD = 0.01  # 1% threshold
FIXED_WIDTH = 17


def format_cell(cell: str,
                width: int = FIXED_WIDTH,
                align: str = "center") -> str:
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

    def __init__(self) -> None:
        self._iteration: int = 0
        self._previous_chi2: Optional[float] = None
        self._last_chi2: Optional[float] = None
        self._last_iteration: Optional[int] = None
        self._best_chi2: Optional[float] = None
        self._best_iteration: Optional[int] = None
        self._fitting_time: Optional[float] = None
        self._headers: List[str] = ["iteration", "χ²", "improvement [%]"]
        self._alignments: List[str] = ["center", "center", "center"]
        self._df_rows: List[List[str]] = []

    def reset(self) -> None:
        self._iteration = 0
        self._previous_chi2 = None
        self._last_chi2 = None
        self._last_iteration = None
        self._best_chi2 = None
        self._best_iteration = None
        self._fitting_time = None

    def track(self,
              residuals: np.ndarray,
              parameters: List[float]) -> np.ndarray:
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

        row: List[str] = []

        # First iteration, initialize tracking
        if self._previous_chi2 is None:
            self._previous_chi2 = reduced_chi2
            self._best_chi2 = reduced_chi2
            self._best_iteration = self._iteration

            row = [
                str(self._iteration),
                f"{reduced_chi2:.2f}",
                ""
            ]

        # Improvement check
        elif (self._previous_chi2 - reduced_chi2) / self._previous_chi2 > SIGNIFICANT_CHANGE_THRESHOLD:
            change_percent = (self._previous_chi2 - reduced_chi2) / self._previous_chi2 * 100

            row = [
                str(self._iteration),
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
    def best_chi2(self) -> Optional[float]:
        return self._best_chi2

    @property
    def best_iteration(self) -> Optional[int]:
        return self._best_iteration

    @property
    def iteration(self) -> int:
        return self._iteration

    @property
    def fitting_time(self) -> Optional[float]:
        return self._fitting_time

    def start_timer(self) -> None:
        self._start_time = time.perf_counter()

    def stop_timer(self) -> None:
        self._end_time = time.perf_counter()
        self._fitting_time = self._end_time - self._start_time

    def start_tracking(self, minimizer_name: str) -> None:
        print(f"🚀 Starting fitting process with '{minimizer_name}'...")
        print("📈 Goodness-of-fit (reduced χ²) change:")

        if is_notebook() and display is not None:
            self._df_rows = []  # Reset notebook tracking
        else:
            # Top border
            print("╒" + "╤".join(["═" * FIXED_WIDTH for _ in self._headers]) + "╕")

            # Header row (all centered)
            header_row = "│" + "│".join([format_cell(h, align="center") for h in self._headers]) + "│"
            print(header_row)

            # Separator
            print("╞" + "╪".join(["═" * FIXED_WIDTH for _ in self._headers]) + "╡")

    def add_tracking_info(self, row: List[str]) -> None:
        if is_notebook() and display is not None and clear_output is not None:
            # Add row to DataFrame, clear previous output, and show updated table
            self._df_rows.append(row)
            clear_output(wait=True)
            render_table(columns_data=self._df_rows,
                         columns_alignment=self._alignments,
                         columns_headers=self._headers)
        else:
            # Alignments for each column
            formatted_row = "│" + "│".join([
                format_cell(cell, align=self._alignments[i])
                for i, cell in enumerate(row)
            ]) + "│"

            print(formatted_row)

    def finish_tracking(self) -> None:
        # Add last iteration as last row
        row: List[str] = [
            str(self._last_iteration),
            f"{self._last_chi2:.2f}" if self._last_chi2 is not None else "",
            ""
        ]
        self.add_tracking_info(row)

        if not is_notebook():
            # Bottom border for terminal only
            print("╘" + "╧".join(["═" * FIXED_WIDTH for _ in range(len(row))]) + "╛")

        # Print best result
        print(f"🏆 Best goodness-of-fit (reduced χ²) is {self._best_chi2:.2f} at iteration {self._best_iteration}")
        print("✅ Fitting complete.")
