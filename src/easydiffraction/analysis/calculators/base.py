# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from abc import ABC
from abc import abstractmethod

import numpy as np

from easydiffraction.datablocks.experiment.item.base import ExperimentBase
from easydiffraction.datablocks.structure.collection import Structures
from easydiffraction.datablocks.structure.item.base import Structure


class CalculatorBase(ABC):
    """Base API for diffraction calculation engines."""

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def engine_imported(self) -> bool:
        pass

    @abstractmethod
    def calculate_structure_factors(
        self,
        structure: Structure,
        experiment: ExperimentBase,
        called_by_minimizer: bool,
    ) -> None:
        """
        Calculate structure factors for a single structure and
        experiment.
        """
        pass

    @abstractmethod
    def calculate_pattern(
        self,
        structure: Structures,  # TODO: Structure?
        experiment: ExperimentBase,
        called_by_minimizer: bool,
    ) -> np.ndarray:
        """
        Calculate the diffraction pattern for a single structure and experiment.

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
        pass
