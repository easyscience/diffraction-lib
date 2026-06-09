# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Time-of-flight powder data range (time-of-flight bounds and step)."""

from __future__ import annotations

import numpy as np

from easydiffraction.core.display_handler import DisplayHandler
from easydiffraction.core.metadata import Compatibility
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import RangeValidator
from easydiffraction.core.variable import NumericDescriptor
from easydiffraction.datablocks.experiment.categories.data_range.base import DataRangeBase
from easydiffraction.datablocks.experiment.categories.data_range.factory import DataRangeFactory
from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum
from easydiffraction.io.cif.handler import CifHandler


@DataRangeFactory.register
class TofPdDataRange(DataRangeBase):
    """
    Time-of-flight powder calculation range.

    Stores the time-of-flight window
    (``time_of_flight_min``/``time_of_flight_max``) and the profile step
    (``time_of_flight_inc``). Unset bounds default to ``NaN`` and are
    filled by projecting the default d-spacing window through the
    instrument TOF calibration.
    """

    type_info = TypeInfo(
        tag='tof-pd',
        description='TOF powder calculation range',
    )
    compatibility = Compatibility(
        scattering_type=frozenset({ScatteringTypeEnum.BRAGG}),
        beam_mode=frozenset({BeamModeEnum.TIME_OF_FLIGHT}),
        sample_form=frozenset({SampleFormEnum.POWDER}),
    )

    def __init__(self) -> None:
        """Initialize the time-of-flight powder data range."""
        super().__init__()

        self._time_of_flight_min = NumericDescriptor(
            name='time_of_flight_min',
            description='Lower time-of-flight bound of the calculation range',
            units='microseconds',
            display_handler=DisplayHandler(
                display_name='TOF min',
                display_units='μs',
                latex_name=r'$\mathrm{TOF}_{\min}$',
                latex_units=r'$\mu\mathrm{s}$',
            ),
            value_spec=AttributeSpec(
                default=np.nan,
                validator=RangeValidator(ge=0),
            ),
            cif_handler=CifHandler(names=['_pd_meas.time_of_flight_range_min']),
        )
        self._time_of_flight_max = NumericDescriptor(
            name='time_of_flight_max',
            description='Upper time-of-flight bound of the calculation range',
            units='microseconds',
            display_handler=DisplayHandler(
                display_name='TOF max',
                display_units='μs',
                latex_name=r'$\mathrm{TOF}_{\max}$',
                latex_units=r'$\mu\mathrm{s}$',
            ),
            value_spec=AttributeSpec(
                default=np.nan,
                validator=RangeValidator(ge=0),
            ),
            cif_handler=CifHandler(names=['_pd_meas.time_of_flight_range_max']),
        )
        self._time_of_flight_inc = NumericDescriptor(
            name='time_of_flight_inc',
            description='Time-of-flight step between calculation points',
            units='microseconds',
            display_handler=DisplayHandler(
                display_name='TOF step',
                display_units='μs',
                latex_name=r'$\mathrm{TOF}_{\mathrm{inc}}$',
                latex_units=r'$\mu\mathrm{s}$',
            ),
            value_spec=AttributeSpec(
                default=np.nan,
                validator=RangeValidator(gt=0),
            ),
            cif_handler=CifHandler(names=['_pd_meas.time_of_flight_range_inc']),
        )

    # ------------------------------------------------------------------
    #  Public properties
    # ------------------------------------------------------------------

    @property
    def time_of_flight_min(self) -> float:
        """Lower time-of-flight bound of the calculation range (μs)."""
        return self._time_of_flight_min.value

    @time_of_flight_min.setter
    def time_of_flight_min(self, value: float) -> None:
        """Set the lower time-of-flight bound (μs)."""
        self._time_of_flight_min.value = value

    @property
    def time_of_flight_max(self) -> float:
        """Upper time-of-flight bound of the calculation range (μs)."""
        return self._time_of_flight_max.value

    @time_of_flight_max.setter
    def time_of_flight_max(self, value: float) -> None:
        """Set the upper time-of-flight bound (μs)."""
        self._time_of_flight_max.value = value

    @property
    def time_of_flight_inc(self) -> float:
        """Time-of-flight step between calculation points (μs)."""
        return self._time_of_flight_inc.value

    @time_of_flight_inc.setter
    def time_of_flight_inc(self, value: float) -> None:
        """Set the time-of-flight step between calculation points (μs)."""
        self._time_of_flight_inc.value = value
