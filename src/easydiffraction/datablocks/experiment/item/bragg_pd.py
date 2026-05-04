# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from easydiffraction.core.metadata import Compatibility
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.datablocks.experiment.categories.background.factory import BackgroundFactory
from easydiffraction.datablocks.experiment.categories.instrument.factory import InstrumentFactory
from easydiffraction.datablocks.experiment.categories.data.refln_pd import PowderCwlReflnData
from easydiffraction.datablocks.experiment.categories.data.refln_pd import PowderTofReflnData
from easydiffraction.datablocks.experiment.item.base import PdExperimentBase
from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum
from easydiffraction.datablocks.experiment.item.factory import ExperimentFactory
from easydiffraction.io.ascii import load_numeric_block
from easydiffraction.utils.logging import console
from easydiffraction.utils.logging import log
from easydiffraction.utils.utils import render_table

if TYPE_CHECKING:
    from easydiffraction.datablocks.experiment.categories.experiment_type import ExperimentType

# Minimum number of columns required in an ASCII data file
_MIN_COLUMNS_XY = 2
_MIN_COLUMNS_XY_SY = 3

# Uncertainty values below this threshold are replaced with 1.0
_MIN_UNCERTAINTY = 0.0001


@ExperimentFactory.register
class BraggPdExperiment(PdExperimentBase):
    """Standard Bragg powder diffraction experiment."""

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

        self._instrument_type: str = InstrumentFactory.default_tag(
            scattering_type=self.type.scattering_type.value,
            beam_mode=self.type.beam_mode.value,
            sample_form=self.type.sample_form.value,
        )
        self._instrument = InstrumentFactory.create(self._instrument_type)
        self._background_type: str = BackgroundFactory.default_tag()
        self._background = BackgroundFactory.create(self._background_type)
        self._refln = self._create_refln_collection()

    def _create_refln_collection(self) -> object:
        """Create the beam-mode-specific calculated reflection collection."""
        beam_mode = self.type.beam_mode.value
        if beam_mode == BeamModeEnum.CONSTANT_WAVELENGTH:
            return PowderCwlReflnData()
        if beam_mode == BeamModeEnum.TIME_OF_FLIGHT:
            return PowderTofReflnData()

        msg = f'Unsupported beam mode for powder reflection data: {beam_mode}.'
        raise ValueError(msg)

    def _load_ascii_data_to_experiment(
        self,
        data_path: str,
    ) -> int:
        """
        Load (x, y, sy) data from an ASCII file into the data category.

        The file format is space/column separated with 2 or 3 columns:
        ``x y [sy]``. If ``sy`` is missing, it is approximated as
        ``sqrt(y)``.

        If ``sy`` has values smaller than ``0.0001``, they are replaced
        with ``1.0``.

        Parameters
        ----------
        data_path : str
            Path to the ASCII data file.

        Returns
        -------
        int
            Number of loaded data points.
        """
        data = load_numeric_block(data_path)

        if data.shape[1] < _MIN_COLUMNS_XY:
            log.error(
                'Data file must have at least two columns: x and y.',
                exc_type=ValueError,
            )
            return 0

        if data.shape[1] < _MIN_COLUMNS_XY_SY:
            log.warning('No uncertainty (sy) column provided. Defaulting to sqrt(y).')

        # Extract x, y data
        x = data[:, 0]
        y = data[:, 1]

        # Round x to 4 decimal places
        x = np.round(x, 4)

        # Determine sy from column 3 if available, otherwise use sqrt(y)
        sy = data[:, 2] if data.shape[1] > _MIN_COLUMNS_XY else np.sqrt(y)

        # Replace values smaller than _MIN_UNCERTAINTY with 1.0
        # TODO: Not used if loading from cif file?
        sy = np.where(sy < _MIN_UNCERTAINTY, 1.0, sy)

        # Set the experiment data
        self.data._create_items_set_xcoord_and_id(x)
        self.data._set_intensity_meas(y)
        self.data._set_intensity_meas_su(sy)

        return len(x)

    # ------------------------------------------------------------------
    #  Instrument (fixed at creation)
    # ------------------------------------------------------------------

    @property
    def instrument(self) -> object:
        """Active instrument model for this experiment."""
        return self._instrument

    @property
    def refln(self) -> object:
        """Calculated reflection metadata for this experiment."""
        return self._refln

    # ------------------------------------------------------------------
    #  Background (switchable-category pattern)
    # ------------------------------------------------------------------

    @property
    def background_type(self) -> object:
        """Current background type enum value."""
        return self._background_type

    @background_type.setter
    def background_type(self, new_type: str) -> None:
        """Set a new background type and recreate background object."""
        if self._background_type == new_type:
            console.paragraph(f"Background type for experiment '{self.name}' already set to")
            console.print(new_type)
            return

        supported = BackgroundFactory.supported_for(
            calculator=self.calculation.calculator_type.value,
        )
        supported_tags = [k.type_info.tag for k in supported]
        if new_type not in supported_tags:
            log.warning(
                f"Unsupported background type '{new_type}'. "
                f'Supported: {supported_tags}. '
                f"For more information, use 'show_background_types()'",
            )
            return

        if len(self._background) > 0:
            log.warning(
                f'Switching background type discards {len(self._background)} '
                f'existing background point(s).',
            )

        self._background = BackgroundFactory.create(new_type)
        self._background_type = new_type
        console.paragraph(f"Background type for experiment '{self.name}' changed to")
        console.print(new_type)

    @property
    def background(self) -> object:
        """Active background model for this experiment."""
        return self._background

    def show_background_types(self) -> None:
        """Print supported background types and mark current type."""
        supported = BackgroundFactory.supported_for(
            calculator=self.calculation.calculator_type.value,
        )
        columns_data = [
            [
                '*' if klass.type_info.tag == self._background_type else '',
                klass.type_info.tag,
                klass.type_info.description,
            ]
            for klass in supported
        ]
        console.paragraph('Background types')
        render_table(
            columns_headers=['', 'Type', 'Description'],
            columns_alignment=['left', 'left', 'left'],
            columns_data=columns_data,
        )
