# SPDX-FileCopyrightText: 2021-2026 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from typing import TYPE_CHECKING

from easydiffraction.experiments.categories.extinction import Extinction
from easydiffraction.experiments.categories.linked_crystal import LinkedCrystal
from easydiffraction.experiments.experiment.base import ScExperimentBase
from easydiffraction.experiments.experiment.instrument_mixin import InstrumentMixin
from easydiffraction.utils.logging import console

if TYPE_CHECKING:
    from easydiffraction.experiments.categories.experiment_type import ExperimentType


class BraggScExperiment(
    InstrumentMixin,
    ScExperimentBase,
):
    """Single crystal experiment class with specific attributes."""

    def __init__(
        self,
        *,
        name: str,
        type: ExperimentType,
    ) -> None:
        super().__init__(name=name, type=type)

        self._linked_crystal = LinkedCrystal()
        self._extinction = Extinction()

    def _load_ascii_data_to_experiment(self, data_path: str) -> None:
        """Load (index_h, index_k, index_l, y, sy) data from an ASCII
        file into the data category.

        The file format is space/column separated with 5 columns:
        ``h k l Fobs sFobs``.
        """
        import numpy as np

        try:
            data = np.loadtxt(data_path)
        except Exception as e:
            raise IOError(f'Failed to read data from {data_path}: {e}') from e

        if data.shape[1] < 5:
            raise ValueError('Data file must have five columns: h, k, l, Fobs, sFobs.')

        # Extract h, k, l
        indices_h: np.ndarray = data[:, 0].astype(int)
        indices_k: np.ndarray = data[:, 1].astype(int)
        indices_l: np.ndarray = data[:, 2].astype(int)

        # Extract Fobs, sFobs data
        y: np.ndarray = data[:, 3]
        sy: np.ndarray = data[:, 4]

        # Set the experiment data
        self.data._set_hkl(indices_h, indices_k, indices_l)
        self.data._set_meas(y)
        self.data._set_meas_su(sy)

        console.paragraph('Data loaded successfully')
        console.print(f"Experiment 🔬 '{self.name}'. Number of data points: {len(indices_h)}")

    @property
    def linked_crystal(self):
        return self._linked_crystal

    @linked_crystal.setter
    def linked_crystal(self, value):
        self._linked_crystal = value

    @property
    def extinction(self):
        return self._extinction

    @extinction.setter
    def extinction(self, value):
        self._extinction = value
