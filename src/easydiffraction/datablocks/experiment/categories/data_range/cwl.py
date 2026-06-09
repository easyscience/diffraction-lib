# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Constant-wavelength powder data range (2θ bounds and step)."""

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
class CwlPdDataRange(DataRangeBase):
    """
    Constant-wavelength powder calculation range.

    Stores the 2θ window (``two_theta_min``/``two_theta_max``) and the
    profile step (``two_theta_inc``). Unset bounds default to ``NaN`` and
    are filled by projecting the default d-spacing window through the
    instrument wavelength.
    """

    type_info = TypeInfo(
        tag='cwl-pd',
        description='CW powder calculation range',
    )
    compatibility = Compatibility(
        scattering_type=frozenset({ScatteringTypeEnum.BRAGG, ScatteringTypeEnum.TOTAL}),
        beam_mode=frozenset({BeamModeEnum.CONSTANT_WAVELENGTH}),
        sample_form=frozenset({SampleFormEnum.POWDER}),
    )

    def __init__(self) -> None:
        """Initialize the constant-wavelength powder data range."""
        super().__init__()

        self._two_theta_min = NumericDescriptor(
            name='two_theta_min',
            description='Lower 2θ bound of the calculation range',
            units='degrees',
            display_handler=DisplayHandler(
                display_name='2θ min',
                display_units='deg',
                latex_name=r'$2\theta_{\min}$',
                latex_units=r'\mathrm{deg}',
            ),
            value_spec=AttributeSpec(
                default=np.nan,
                validator=RangeValidator(ge=0, le=180),
            ),
            cif_handler=CifHandler(names=['_pd_meas.2theta_range_min']),
        )
        self._two_theta_max = NumericDescriptor(
            name='two_theta_max',
            description='Upper 2θ bound of the calculation range',
            units='degrees',
            display_handler=DisplayHandler(
                display_name='2θ max',
                display_units='deg',
                latex_name=r'$2\theta_{\max}$',
                latex_units=r'\mathrm{deg}',
            ),
            value_spec=AttributeSpec(
                default=np.nan,
                validator=RangeValidator(ge=0, le=180),
            ),
            cif_handler=CifHandler(names=['_pd_meas.2theta_range_max']),
        )
        self._two_theta_inc = NumericDescriptor(
            name='two_theta_inc',
            description='2θ step between calculation points',
            units='degrees',
            display_handler=DisplayHandler(
                display_name='2θ step',
                display_units='deg',
                latex_name=r'$2\theta_{\mathrm{inc}}$',
                latex_units=r'\mathrm{deg}',
            ),
            value_spec=AttributeSpec(
                default=np.nan,
                validator=RangeValidator(gt=0, le=180),
            ),
            cif_handler=CifHandler(names=['_pd_meas.2theta_range_inc']),
        )

    # ------------------------------------------------------------------
    #  Public properties
    # ------------------------------------------------------------------

    @property
    def two_theta_min(self) -> float:
        """Lower 2θ bound of the calculation range (deg)."""
        return self._two_theta_min.value

    @two_theta_min.setter
    def two_theta_min(self, value: float) -> None:
        """Set the lower 2θ bound of the calculation range (deg)."""
        self._two_theta_min.value = value

    @property
    def two_theta_max(self) -> float:
        """Upper 2θ bound of the calculation range (deg)."""
        return self._two_theta_max.value

    @two_theta_max.setter
    def two_theta_max(self, value: float) -> None:
        """Set the upper 2θ bound of the calculation range (deg)."""
        self._two_theta_max.value = value

    @property
    def two_theta_inc(self) -> float:
        """2θ step between calculation points (deg)."""
        return self._two_theta_inc.value

    @two_theta_inc.setter
    def two_theta_inc(self, value: float) -> None:
        """Set the 2θ step between calculation points (deg)."""
        self._two_theta_inc.value = value
