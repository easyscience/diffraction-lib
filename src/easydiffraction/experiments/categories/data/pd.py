from __future__ import annotations

from typing import List

import numpy as np
from scipy.interpolate import interp1d
from typing import Optional

from easydiffraction.experiments.experiment.enums import BeamModeEnum
from easydiffraction.experiments.experiment.enums import PeakProfileTypeEnum
from easydiffraction.experiments.experiment.enums import ScatteringTypeEnum

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

class PdDataPointBaseMixin:
    """Single base data point mixin for powder diffraction data."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._point_id = StringDescriptor(
            name='point_id',
            description='Identifier for this data point in the dataset.',
            value_spec=AttributeSpec(
                type_=DataTypes.STRING,
                default='0',
                # TODO: the following pattern is valid for dict key
                #  (keywords are not checked). CIF label is less strict.
                #  Do we need conversion between CIF and internal label?
                content_validator=RegexValidator(pattern=r'^[A-Za-z0-9_]*$'),
            ),
            cif_handler=CifHandler(
                names=[
                    '_pd_data.point_id',
                ]
            ),
        )
        self._d_spacing = NumericDescriptor(
            name='d_spacing',
            description='d-spacing value corresponding to this data point.',
            value_spec=AttributeSpec(
                type_=DataTypes.NUMERIC,
                default=0.0,
                content_validator=RangeValidator(ge=0),
            ),
            cif_handler=CifHandler(
                names=[
                    '_pd_proc.d_spacing',
                ]
            ),
        )
        self._intensity_meas = NumericDescriptor(
            name='intensity_meas',
            description='Intensity recorded at each measurement point as a function of angle/time',
            value_spec=AttributeSpec(
                type_=DataTypes.NUMERIC,
                default=0.0,
                content_validator=RangeValidator(ge=0),
            ),
            cif_handler=CifHandler(
                names=[
                    '_pd_meas.intensity_total',
                ]
            ),
        )
        self._intensity_meas_su = NumericDescriptor(
            name='intensity_meas_su',
            description='Standard uncertainty of the measured intensity at this data point.',
            value_spec=AttributeSpec(
                type_=DataTypes.NUMERIC,
                default=0.0,
                content_validator=RangeValidator(ge=0),
            ),
            cif_handler=CifHandler(
                names=[
                    '_pd_meas.intensity_total_su',
                ]
            ),
        )
        self._intensity_calc = NumericDescriptor(
            name='intensity_calc',
            description='Intensity value for a computed diffractogram at this data point.',
            value_spec=AttributeSpec(
                type_=DataTypes.NUMERIC,
                default=0.0,
                content_validator=RangeValidator(ge=0),
            ),
            cif_handler=CifHandler(
                names=[
                    '_pd_calc.intensity_total',
                ]
            ),
        )
        self._intensity_bkg = NumericDescriptor(
            name='intensity_bkg',
            description='Intensity value for a computed background at this data point.',
            value_spec=AttributeSpec(
                type_=DataTypes.NUMERIC,
                default=0.0,
                content_validator=RangeValidator(ge=0),
            ),
            cif_handler=CifHandler(
                names=[
                    '_pd_calc.intensity_bkg',
                ]
            ),
        )
        self._refinement_status = StringDescriptor(
            name='refinement_status',
            description='Status code of the data point in the structure refinement process.',
            value_spec=AttributeSpec(
                type_=DataTypes.STRING,
                default='incl', # TODO: Make Enum
                content_validator=MembershipValidator(allowed=['incl', 'excl']),
            ),
            cif_handler=CifHandler(
                names=[
                    '_pd_data.refinement_status',
                ]
            ),
        )

        # TODO: Temporary deletion
        #del self._d_spacing
        #del self._intensity_calc
        #del self._intensity_bkg

    @property
    def point_id(self) -> NumericDescriptor:
        return self._point_id

    @property
    def d_spacing(self) -> NumericDescriptor:
        return self._d_spacing

    @property
    def intensity_meas(self) -> NumericDescriptor:
        return self._intensity_meas

    @property
    def intensity_meas_su(self) -> NumericDescriptor:
        return self._intensity_meas_su

    @property
    def intensity_calc(self) -> NumericDescriptor:
        return self._intensity_calc

    @property
    def intensity_bkg(self) -> NumericDescriptor:
        return self._intensity_bkg

    @property
    def refinement_status(self) -> StringDescriptor:
        return self._refinement_status



class PdCwlDataPointMixin:
    """Mixin for powder diffraction data points with constant wavelength."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._two_theta = NumericDescriptor(
            name='two_theta',
            description='Measured 2θ diffraction angle.',
            value_spec=AttributeSpec(
                type_=DataTypes.NUMERIC,
                default=0.0,
                content_validator=RangeValidator(ge=0, le=180),
            ),
            units='deg',
            cif_handler=CifHandler(
                names=[
                    '_pd_proc.2theta_scan',
                    '_pd_meas.2theta_scan',
                ]
            ),
        )

    @property
    def two_theta(self) -> NumericDescriptor:
        return self._two_theta

class PdTofDataPointMixin:
    """Mixin for powder diffraction data points with time-of-flight."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._time_of_flight = NumericDescriptor(
            name='time_of_flight',
            description='Measured time for time-of-flight neutron measurement.',
            value_spec=AttributeSpec(
                type_=DataTypes.NUMERIC,
                default=0.0,
                content_validator=RangeValidator(ge=0),
            ),
            units='µs',
            cif_handler=CifHandler(
                names=[
                    '_pd_meas.time_of_flight',
                ]
            ),
        )

    @property
    def time_of_flight(self) -> NumericDescriptor:
        return self._time_of_flight

class PdCwlDataPoint(
    PdDataPointBaseMixin,
    PdCwlDataPointMixin,
    CategoryItem, # Must be last to ensure mixins initialized first
):
    """Powder diffraction data point for constant-wavelength experiments."""

    def __init__(self) -> None:
        super().__init__()
        self._identity.category_code = 'pd_data'
        self._identity.category_entry_name = lambda: str(self.point_id.value)


class PdTofDataPoint(
    CategoryItem,
    PdDataPointBaseMixin,
    PdTofDataPointMixin
):
    """Powder diffraction data point for time-of-flight experiments."""

    def __init__(self) -> None:
        super().__init__()
        self._identity.category_code = 'pd_data'
        self._identity.category_entry_name = lambda: str(self.point_id.value)




class PdCwlData(CategoryCollection):
    # TODO: ???
    #_description: str = 'Powder diffraction data points for constant-wavelength experiments.'

    # Redefine update priority to ensure data updated after other
    # categories. Higher number = runs later. Default for other categories,
    # e.g., background and excluded regions are 10 by default
    _update_priority = 100

    def __init__(self):
        super().__init__(item_type=PdCwlDataPoint)

    def _set_calc(self, values) -> None:
        """Helper method to set calculated intensity. To be used internally by calculators."""
        for p, v in zip(self._items, values, strict=True):
            p.intensity_calc._value = v

    def _set_bkg(self, values) -> None:
        """Helper method to set background intensity. To be used internally by calculators."""
        for p, v in zip(self._items, values, strict=True):
            p.intensity_bkg._value = v

    def _set_refinement_status(self, values) -> None:
        """Helper method to set refinement status. To be used internally by refiners."""
        for p, v in zip(self._items, values, strict=True):
            if v:
                p.refinement_status._value = 'incl'
            elif not v:
                p.refinement_status._value = 'excl'
            else:
                raise ValueError(
                    f'Invalid refinement status value: {v}. '
                    f'Expected boolean True/False.'
                )

    @property
    def x(self) -> np.ndarray:
        """Get the 2θ values for all data points in this collection."""
        return np.fromiter((p.two_theta.value for p in self._items), dtype=float)

    @property
    def meas(self) -> np.ndarray:
        return np.fromiter((p.intensity_meas.value for p in self._items), dtype=float)

    @property
    def meas_su(self) -> np.ndarray:
        return np.fromiter((p.intensity_meas_su.value for p in self._items), dtype=float)

    @property
    def calc(self) -> np.ndarray:
        return np.fromiter((p.intensity_calc.value for p in self._items), dtype=float)

    @property
    def bkg(self) -> np.ndarray:
        return np.fromiter((p.intensity_bkg.value for p in self._items), dtype=float)

    @property
    def refinement_status(self) -> np.ndarray:
        return np.fromiter((p.refinement_status.value for p in self._items), dtype=object)

    def _update(self, called_by_minimizer=False):
        experiment = self._parent
        experiments = experiment._parent
        project = experiments._parent
        sample_models = project.sample_models
        #calculator = experiment.calculator
        calculator = project.analysis.calculator

        initial_y_calc = np.zeros_like(self.x)
        y_calc_scaled = initial_y_calc
        for linked_phase in experiment.linked_phases:
            sample_model_id = linked_phase._identity.category_entry_name
            sample_model_scale = linked_phase.scale.value
            sample_model = sample_models[sample_model_id]

            sample_model_y_calc = calculator._calculate_single_model_pattern(
                sample_model,
                experiment,
                called_by_minimizer=called_by_minimizer,
            )

            sample_model_y_calc_scaled = sample_model_scale * sample_model_y_calc
            y_calc_scaled += sample_model_y_calc_scaled

        self._set_calc(y_calc_scaled + self.bkg)

        # TODO: Reduce calculation for the 'incl' points (refinement_status) only



class PdTofData(CategoryCollection):
    # TODO: ???
    #_description: str = 'Powder diffraction data points for time-of-flight experiments.'

    def __init__(self):
        super().__init__(item_type=PdTofDataPoint)



class DataFactory:
    """Factory for creating powder diffraction data collections."""

    _supported = {
        SampleFormEnum.POWDER: {
            BeamModeEnum.CONSTANT_WAVELENGTH: PdCwlData,
            BeamModeEnum.TIME_OF_FLIGHT: PdTofData,
        },
    }

    @classmethod
    def create(
            cls,
            *,
            sample_form: Optional[SampleFormEnum] = None,
            beam_mode: Optional[BeamModeEnum] = None,
    ) -> CategoryCollection:
        """Create a data collection for the given configuration."""

        supported_sample_forms = list(cls._supported.keys())
        if sample_form not in supported_sample_forms:
            raise ValueError(
                f"Unsupported sample form: '{sample_form}'.\n"
                f'Supported sample forms: {supported_sample_forms}'
            )
        supported_beam_modes = list(cls._supported[sample_form].keys())
        if beam_mode not in supported_beam_modes:
            raise ValueError(
                f"Unsupported beam mode: '{beam_mode}' for scattering type: "
                f"'{sample_form}'.\n Supported beam modes: '{supported_beam_modes}'"
            )

        if sample_form is None:
            sample_form = SampleFormEnum.default()
        if beam_mode is None:
            beam_mode = BeamModeEnum.default()

        data_class = cls._supported[sample_form][beam_mode]
        data_obj = data_class()

        return data_obj

