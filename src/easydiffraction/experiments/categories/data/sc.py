from __future__ import annotations

from typing import List

import numpy as np
from scipy.interpolate import interp1d
from typing import Optional

from easydiffraction.experiments.experiment.enums import BeamModeEnum
from easydiffraction.experiments.experiment.enums import PeakProfileTypeEnum
from easydiffraction.experiments.experiment.enums import ScatteringTypeEnum
from easydiffraction.utils.utils import tof_to_d
from easydiffraction.utils.utils import twotheta_to_d
from easydiffraction.core.category import CategoryItem, CategoryCollection
from easydiffraction.core.parameters import NumericDescriptor, StringDescriptor
from easydiffraction.core.parameters import Parameter
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import DataTypes
from easydiffraction.core.validation import RangeValidator, RegexValidator, MembershipValidator
from easydiffraction.experiments.categories.background.base import BackgroundBase
from easydiffraction.experiments.experiment.enums import SampleFormEnum, BeamModeEnum
from easydiffraction.io.cif.handler import CifHandler
from easydiffraction.utils.logging import console
from easydiffraction.utils.logging import log
from easydiffraction.utils.utils import render_table

class Refln:

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._index_h = StringDescriptor(
            name='index_h',
            description='...',
            value_spec=AttributeSpec(
                type_=DataTypes.NUMERIC,
                default=0.0,
                content_validator=RangeValidator(),
            ),
            cif_handler=CifHandler(
                names=[
                    '_refln.index_h',
                ]
            ),
        )
        self._index_k = StringDescriptor(
            name='index_k',
            description='...',
            value_spec=AttributeSpec(
                type_=DataTypes.NUMERIC,
                default=0.0,
                content_validator=RangeValidator(),
            ),
            cif_handler=CifHandler(
                names=[
                    '_refln.index_k',
                ]
            ),
        )
        self._index_l = StringDescriptor(
            name='index_l',
            description='...',
            value_spec=AttributeSpec(
                type_=DataTypes.NUMERIC,
                default=0.0,
                content_validator=RangeValidator(),
            ),
            cif_handler=CifHandler(
                names=[
                    '_refln.index_l',
                ]
            ),
        )
        self._intensity_meas = NumericDescriptor(
            name='intensity_meas',
            description='...',
            value_spec=AttributeSpec(
                type_=DataTypes.NUMERIC,
                default=0.0,
                content_validator=RangeValidator(ge=0),
            ),
            cif_handler=CifHandler(
                names=[
                    '_refln.intensity_meas',
                ]
            ),
        )
        self._intensity_meas_su = NumericDescriptor(
            name='intensity_meas_su',
            description='...',
            value_spec=AttributeSpec(
                type_=DataTypes.NUMERIC,
                default=0.0,
                content_validator=RangeValidator(ge=0),
            ),
            cif_handler=CifHandler(
                names=[
                    '_refln.intensity_meas_su',
                ]
            ),
        )

    class ReflnData(CategoryCollection):
        _update_priority = 100

        def __init__(self):
            super().__init__(item_type=Refln)