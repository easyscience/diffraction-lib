# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from typing import TYPE_CHECKING

from easydiffraction.core.metadata import Compatibility
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.datablocks.experiment.item.base import ScExperimentBase
from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum
from easydiffraction.datablocks.experiment.item.factory import ExperimentFactory
from easydiffraction.io.ascii import load_numeric_block
from easydiffraction.utils.logging import log

if TYPE_CHECKING:
    from easydiffraction.datablocks.experiment.categories.experiment_type import ExperimentType

# Minimum number of columns required in CWL and TOF single-crystal files
_MIN_COLUMNS_CWL_SC = 5
_MIN_COLUMNS_TOF_SC = 6


@ExperimentFactory.register
class CwlScExperiment(ScExperimentBase):
    """Bragg constant-wavelength single-crystal experiment."""

    type_info = TypeInfo(
        tag='bragg-sc-cwl',
        description='Bragg CWL single-crystal experiment',
    )
    compatibility = Compatibility(
        scattering_type=frozenset({ScatteringTypeEnum.BRAGG}),
        sample_form=frozenset({SampleFormEnum.SINGLE_CRYSTAL}),
        beam_mode=frozenset({BeamModeEnum.CONSTANT_WAVELENGTH}),
    )

    def __init__(
        self,
        *,
        name: str,
        type: ExperimentType,
    ) -> None:
        super().__init__(name=name, type=type)

    def _load_ascii_data_to_experiment(self, data_path: str) -> int:
        """
        Load measured data from an ASCII file into the data category.

        The file format is space/column separated with 5 columns: ``h k
        l Iobs sIobs``.

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

        if data.shape[1] < _MIN_COLUMNS_CWL_SC:
            log.error(
                'Data file must have at least 5 columns: h, k, l, Iobs, sIobs.',
                exc_type=ValueError,
            )
            return 0

        # Extract Miller indices h, k, l
        indices_h = data[:, 0].astype(int)
        indices_k = data[:, 1].astype(int)
        indices_l = data[:, 2].astype(int)

        # Extract intensities and their standard uncertainties
        integrated_intensities = data[:, 3]
        integrated_intensities_su = data[:, 4]

        # Set the experiment data
        self.data._create_items_set_hkl_and_id(indices_h, indices_k, indices_l)
        self.data._set_intensity_meas(integrated_intensities)
        self.data._set_intensity_meas_su(integrated_intensities_su)

        return len(indices_h)


@ExperimentFactory.register
class TofScExperiment(ScExperimentBase):
    """Bragg time-of-flight single-crystal experiment."""

    type_info = TypeInfo(
        tag='bragg-sc-tof',
        description='Bragg TOF single-crystal experiment',
    )
    compatibility = Compatibility(
        scattering_type=frozenset({ScatteringTypeEnum.BRAGG}),
        sample_form=frozenset({SampleFormEnum.SINGLE_CRYSTAL}),
        beam_mode=frozenset({BeamModeEnum.TIME_OF_FLIGHT}),
    )

    def __init__(
        self,
        *,
        name: str,
        type: ExperimentType,
    ) -> None:
        super().__init__(name=name, type=type)

    def _load_ascii_data_to_experiment(self, data_path: str) -> int:
        """
        Load measured data from an ASCII file into the data category.

        The file format is space/column separated with 6 columns: ``h k
        l Iobs sIobs wavelength``.

        Parameters
        ----------
        data_path : str
            Path to the ASCII data file.

        Returns
        -------
        int
            Number of loaded data points.
        """
        try:
            data = load_numeric_block(data_path)
        except OSError as e:
            log.error(
                f'Failed to read data from {data_path}: {e}',
                exc_type=IOError,
            )
            return 0

        if data.shape[1] < _MIN_COLUMNS_TOF_SC:
            log.error(
                'Data file must have at least 6 columns: h, k, l, Iobs, sIobs, wavelength.',
                exc_type=ValueError,
            )
            return 0

        # Extract Miller indices h, k, l
        indices_h = data[:, 0].astype(int)
        indices_k = data[:, 1].astype(int)
        indices_l = data[:, 2].astype(int)

        # Extract intensities and their standard uncertainties
        integrated_intensities = data[:, 3]
        integrated_intensities_su = data[:, 4]

        # Extract wavelength values
        wavelength = data[:, 5]

        # Set the experiment data
        self.data._create_items_set_hkl_and_id(indices_h, indices_k, indices_l)
        self.data._set_intensity_meas(integrated_intensities)
        self.data._set_intensity_meas_su(integrated_intensities_su)
        self.data._set_wavelength(wavelength)

        return len(indices_h)
