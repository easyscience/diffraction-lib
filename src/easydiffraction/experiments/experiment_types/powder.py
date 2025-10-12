# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from easydiffraction.experiments.collections.background import BackgroundFactory
from easydiffraction.experiments.collections.background import BackgroundTypeEnum
from easydiffraction.experiments.experiment_types.base import BasePowderExperiment
from easydiffraction.experiments.experiment_types.base import InstrumentMixin
from easydiffraction.utils.formatting import paragraph
from easydiffraction.utils.formatting import warning
from easydiffraction.utils.utils import render_table

if TYPE_CHECKING:
    from easydiffraction.experiments.components.experiment_type import ExperimentType


class PowderExperiment(InstrumentMixin, BasePowderExperiment):
    """Powder experiment class with specific attributes.

    Wraps background, peak profile, and linked phases.
    """

    def __init__(
        self,
        *,
        name: str,
        type: ExperimentType,
    ) -> None:
        super().__init__(name=name, type=type)

        self._background_type: BackgroundTypeEnum = BackgroundTypeEnum.default()
        self._background = BackgroundFactory.create(background_type=self.background_type)

    @property
    def background(self):
        return self._background

    @background.setter
    def background(self, value):
        self._background = value

    # -------------
    # Measured data
    # -------------

    def _load_ascii_data_to_experiment(self, data_path: str) -> None:
        """Loads x, y, sy values from an ASCII data file into the
        experiment.

        The file must be structured as:
            x  y  sy
        """
        try:
            data = np.loadtxt(data_path)
        except Exception as e:
            raise IOError(f'Failed to read data from {data_path}: {e}') from e

        if data.shape[1] < 2:
            raise ValueError('Data file must have at least two columns: x and y.')

        if data.shape[1] < 3:
            print('Warning: No uncertainty (sy) column provided. Defaulting to sqrt(y).')

        # Extract x, y data
        x: np.ndarray = data[:, 0]
        y: np.ndarray = data[:, 1]

        # Round x to 4 decimal places
        x = np.round(x, 4)

        # Determine sy from column 3 if available, otherwise use sqrt(y)
        sy: np.ndarray = data[:, 2] if data.shape[1] > 2 else np.sqrt(y)

        # Replace values smaller than 0.0001 with 1.0
        sy = np.where(sy < 0.0001, 1.0, sy)

        # Attach the data to the experiment's datastore
        self.datastore.full_x = x
        self.datastore.full_meas = y
        self.datastore.full_meas_su = sy
        self.datastore.x = x
        self.datastore.meas = y
        self.datastore.meas_su = sy
        self.datastore.excluded = np.full(x.shape, fill_value=False, dtype=bool)

        print(paragraph('Data loaded successfully'))
        print(f"Experiment 🔬 '{self.name}'. Number of data points: {len(x)}")

    @property
    def background_type(self):
        return self._background_type

    @background_type.setter
    def background_type(self, new_type):
        if new_type not in BackgroundFactory._supported:
            supported_types = list(BackgroundFactory._supported.keys())
            print(warning(f"Unknown background type '{new_type}'"))
            print(f'Supported background types: {supported_types}')
            print("For more information, use 'show_supported_background_types()'")
            return
        self.background = BackgroundFactory.create(new_type)
        self._background_type = new_type
        print(paragraph(f"Background type for experiment '{self.name}' changed to"))
        print(new_type)

    def show_supported_background_types(self):
        columns_headers = ['Background type', 'Description']
        columns_alignment = ['left', 'left']
        columns_data = []
        for bt in BackgroundFactory._supported:
            columns_data.append([bt.value, bt.description()])

        print(paragraph('Supported background types'))
        render_table(
            columns_headers=columns_headers,
            columns_alignment=columns_alignment,
            columns_data=columns_data,
        )

    def show_current_background_type(self):
        print(paragraph('Current background type'))
        print(self.background_type)
