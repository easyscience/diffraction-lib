# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Abstract base API for diffraction calculation backends."""

from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np

    from easydiffraction.datablocks.experiment.item.base import ExperimentBase
    from easydiffraction.datablocks.structure.collection import Structures
    from easydiffraction.datablocks.structure.item.base import Structure


@dataclass(frozen=True)
class PowderReflnRecord:
    """Calculated powder reflection metadata for one reflection row."""

    phase_id: str
    d_spacing: float
    sin_theta_over_lambda: float
    index_h: int
    index_k: int
    index_l: int
    f_calc: float
    f_squared_calc: float
    two_theta: float | None = None
    time_of_flight: float | None = None


class CalculatorBase(ABC):
    """Base API for diffraction calculation engines."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Short identifier of the calculation engine."""

    @property
    @abstractmethod
    def engine_imported(self) -> bool:
        """True if the underlying calculation library is available."""

    @abstractmethod
    def calculate_structure_factors(
        self,
        structure: Structure,
        experiment: ExperimentBase,
        *,
        called_by_minimizer: bool,
    ) -> None:
        """Calculate structure factors for one experiment."""

    @abstractmethod
    def calculate_pattern(
        self,
        structure: Structures,  # TODO: Structure?
        experiment: ExperimentBase,
        *,
        called_by_minimizer: bool,
    ) -> np.ndarray:
        """
        Calculate diffraction pattern for one structure-experiment pair.

        Parameters
        ----------
        structure : Structures
            The structure object.
        experiment : ExperimentBase
            The experiment object.
        called_by_minimizer : bool
            Whether the calculation is called by a minimizer. Default is
            False.

        Returns
        -------
        np.ndarray
            The calculated diffraction pattern as a NumPy array.
        """

    def last_powder_refln_records(
        self,
        structure: Structure,
        experiment: ExperimentBase,
        *,
        phase_id: str,
    ) -> list[PowderReflnRecord] | None:
        """
        Return the last powder reflection records for one phase.

        Backends that do not expose powder reflection metadata return
        ``None`` so callers can clear stale reflection rows and warn.
        """
        del self, structure, experiment, phase_id
        return None
