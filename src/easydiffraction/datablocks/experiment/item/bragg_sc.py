# SPDX-FileCopyrightText: 2021-2026 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from easydiffraction.datablocks.experiment.item.base import ScExperimentBase
from easydiffraction.utils.logging import console
from easydiffraction.utils.logging import log

if TYPE_CHECKING:
    from easydiffraction.datablocks.experiment.categories.experiment_type import ExperimentType


class CwlScExperiment(ScExperimentBase):
    """Standard (Bragg) constant wavelength single srystal experiment
    class with specific attributes.
    """

    def __init__(
        self,
        *,
        name: str,
        type: ExperimentType,
    ) -> None:
        super().__init__(name=name, type=type)

    def _load_ascii_data_to_experiment(self, data_path: str) -> None:
        """Load measured data from an ASCII file into the data category.

        The file format is space/column separated with 5 columns:
        ``h k l Iobs sIobs``.
        """
        try:
            data = np.loadtxt(data_path)
        except Exception as e:
            log.error(
                f'Failed to read data from {data_path}: {e}',
                exc_type=IOError,
            )
            return

        if data.shape[1] < 5:
            log.error(
                'Data file must have at least 5 columns: h, k, l, Iobs, sIobs.',
                exc_type=ValueError,
            )
            return

        # Extract Miller indices h, k, l
        indices_h: np.ndarray = data[:, 0].astype(int)
        indices_k: np.ndarray = data[:, 1].astype(int)
        indices_l: np.ndarray = data[:, 2].astype(int)

        # Extract intensities and their standard uncertainties
        integrated_intensities: np.ndarray = data[:, 3]
        integrated_intensities_su: np.ndarray = data[:, 4]

        # Set the experiment data
        self.data._create_items_set_hkl_and_id(indices_h, indices_k, indices_l)
        self.data._set_intensity_meas(integrated_intensities)
        self.data._set_intensity_meas_su(integrated_intensities_su)

        console.paragraph('Data loaded successfully')
        console.print(f"Experiment 🔬 '{self.name}'. Number of data points: {len(indices_h)}")


class TofScExperiment(ScExperimentBase):
    """Standard (Bragg) time-of-flight single srystal experiment class
    with specific attributes.
    """

    def __init__(
        self,
        *,
        name: str,
        type: ExperimentType,
    ) -> None:
        super().__init__(name=name, type=type)

    def _load_ascii_data_to_experiment(self, data_path: str) -> None:
        """Load measured data from an ASCII file into the data category.

        The file format is space/column separated with 6 columns:
        ``h k l Iobs sIobs wavelength``.
        """
        try:
            data = np.loadtxt(data_path)
        except Exception as e:
            log.error(
                f'Failed to read data from {data_path}: {e}',
                exc_type=IOError,
            )
            return

        if data.shape[1] < 6:
            log.error(
                'Data file must have at least 6 columns: h, k, l, Iobs, sIobs, wavelength.',
                exc_type=ValueError,
            )
            return

        # Extract Miller indices h, k, l
        indices_h: np.ndarray = data[:, 0].astype(int)
        indices_k: np.ndarray = data[:, 1].astype(int)
        indices_l: np.ndarray = data[:, 2].astype(int)

        # Extract intensities and their standard uncertainties
        integrated_intensities: np.ndarray = data[:, 3]
        integrated_intensities_su: np.ndarray = data[:, 4]

        # Extract wavelength values
        wavelength: np.ndarray = data[:, 5]

        # Set the experiment data
        self.data._create_items_set_hkl_and_id(indices_h, indices_k, indices_l)
        self.data._set_intensity_meas(integrated_intensities)
        self.data._set_intensity_meas_su(integrated_intensities_su)
        self.data._set_wavelength(wavelength)

        console.paragraph('Data loaded successfully')
        console.print(f"Experiment 🔬 '{self.name}'. Number of data points: {len(indices_h)}")
