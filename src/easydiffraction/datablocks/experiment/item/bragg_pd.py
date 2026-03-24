# SPDX-FileCopyrightText: 2021-2026 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from easydiffraction.core.metadata import Compatibility
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.datablocks.experiment.categories.background.factory import BackgroundFactory
from easydiffraction.datablocks.experiment.categories.instrument.factory import InstrumentFactory
from easydiffraction.datablocks.experiment.item.base import PdExperimentBase
from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum
from easydiffraction.datablocks.experiment.item.factory import ExperimentFactory
from easydiffraction.utils.logging import console
from easydiffraction.utils.logging import log

if TYPE_CHECKING:
    from easydiffraction.datablocks.experiment.categories.experiment_type import ExperimentType


@ExperimentFactory.register
class BraggPdExperiment(PdExperimentBase):
    """Standard (Bragg) Powder Diffraction experiment class with
    specific attributes.
    """

    type_info = TypeInfo(
        tag='bragg-pd',
        description='Bragg powder diffraction experiment',
    )
    compatibility = Compatibility(
        scattering_type=frozenset({ScatteringTypeEnum.BRAGG}),
        sample_form=frozenset({SampleFormEnum.POWDER}),
        beam_mode=frozenset({BeamModeEnum.CONSTANT_WAVELENGTH, BeamModeEnum.TIME_OF_FLIGHT}),
    )

    def __init__(
        self,
        *,
        name: str,
        type: ExperimentType,
    ) -> None:
        super().__init__(name=name, type=type)

        self._instrument = InstrumentFactory.create_default_for(
            scattering_type=self.type.scattering_type.value,
            beam_mode=self.type.beam_mode.value,
            sample_form=self.type.sample_form.value,
        )
        self._background_type: str = BackgroundFactory.default_tag()
        self._background = BackgroundFactory.create(self._background_type)

    def _load_ascii_data_to_experiment(self, data_path: str) -> None:
        """Load (x, y, sy) data from an ASCII file into the data
        category.

        The file format is space/column separated with 2 or 3 columns:
        ``x y [sy]``. If ``sy`` is missing, it is approximated as
        ``sqrt(y)``.

        If ``sy`` has values smaller than ``0.0001``, they are replaced
        with ``1.0``.
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
        # TODO: Not used if loading from cif file?
        sy = np.where(sy < 0.0001, 1.0, sy)

        # Set the experiment data
        self.data._create_items_set_xcoord_and_id(x)
        self.data._set_intensity_meas(y)
        self.data._set_intensity_meas_su(sy)

        console.paragraph('Data loaded successfully')
        console.print(f"Experiment 🔬 '{self.name}'. Number of data points: {len(x)}")

    @property
    def instrument(self):
        return self._instrument

    @property
    def background_type(self):
        """Current background type enum value."""
        return self._background_type

    @background_type.setter
    def background_type(self, new_type):
        """Set a new background type and recreate background object."""
        if self._background_type == new_type:
            console.paragraph(f"Background type for experiment '{self.name}' already set to")
            console.print(new_type)
            return

        supported_tags = BackgroundFactory.supported_tags()
        if new_type not in supported_tags:
            log.warning(
                f"Unsupported background type '{new_type}'. "
                f'Supported: {supported_tags}. '
                f"For more information, use 'show_supported_background_types()'",
            )
            return

        self._background = BackgroundFactory.create(new_type)
        self._background_type = new_type
        console.paragraph(f"Background type for experiment '{self.name}' changed to")
        console.print(new_type)

    @property
    def background(self):
        return self._background

    def show_supported_background_types(self):
        """Print a table of supported background types."""
        BackgroundFactory.show_supported()

    def show_current_background_type(self):
        """Print the currently used background type."""
        console.paragraph('Current background type')
        console.print(self.background_type)
