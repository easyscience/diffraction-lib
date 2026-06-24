# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Total scattering (PDF) powder experiment datablock item."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from easydiffraction.core.metadata import Compatibility
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.datablocks.experiment.item.base import PdExperimentBase
from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum
from easydiffraction.datablocks.experiment.item.factory import ExperimentFactory
from easydiffraction.utils.logging import log

if TYPE_CHECKING:
    from easydiffraction.datablocks.experiment.categories.experiment_type import ExperimentType

# Minimum number of columns required in an ASCII data file
_MIN_COLUMNS_XY = 2
_MIN_COLUMNS_XY_SY = 3


@ExperimentFactory.register
class TotalPdExperiment(PdExperimentBase):
    """PDF experiment class with specific attributes."""

    type_info = TypeInfo(
        tag='total-pd',
        description='Total scattering (PDF) powder experiment',
    )
    compatibility = Compatibility(
        scattering_type=frozenset({ScatteringTypeEnum.TOTAL}),
        sample_form=frozenset({SampleFormEnum.POWDER}),
        beam_mode=frozenset({BeamModeEnum.CONSTANT_WAVELENGTH, BeamModeEnum.TIME_OF_FLIGHT}),
    )

    def __init__(
        self,
        name: str,
        experiment_type: ExperimentType,
    ) -> None:
        super().__init__(name=name, experiment_type=experiment_type)

    def _load_ascii_data_to_experiment(self, data_path: str) -> int:
        """
        Load x, y, sy values from an ASCII file into the experiment.

        The file must be structured as:     x  y  sy

        Parameters
        ----------
        data_path : str
            Path to the ASCII data file.

        Returns
        -------
        int
            Number of loaded data points.

        Raises
        ------
        ImportError
            If the ``diffpy`` package is not installed.
        OSError
            If the data file cannot be read.
        ValueError
            If the data file has fewer than two columns.
        """
        try:
            from diffpy.utils.parsers import load_data  # noqa: PLC0415
        except ImportError:
            msg = 'diffpy module not found.'
            raise ImportError(msg) from None
        try:
            data = load_data(data_path)
        except Exception as e:
            msg = f'Failed to read data from {data_path}: {e}'
            raise OSError(msg) from e

        if data.shape[1] < _MIN_COLUMNS_XY:
            msg = 'Data file must have at least two columns: x and y.'
            raise ValueError(msg)

        default_sy = 0.03
        if data.shape[1] < _MIN_COLUMNS_XY_SY:
            log.warning(f'No uncertainty (sy) column provided. Defaulting to {default_sy}.')

        x = data[:, 0]
        y = data[:, 1]
        sy = (
            data[:, 2]
            if data.shape[1] > _MIN_COLUMNS_XY
            else np.full_like(y, fill_value=default_sy)
        )

        self.data._create_items_set_xcoord_and_id(x)
        self.data._set_g_r_meas(y)
        self.data._set_g_r_meas_su(sy)

        return len(x)
