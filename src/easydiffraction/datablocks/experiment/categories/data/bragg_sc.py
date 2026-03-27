# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import numpy as np

from easydiffraction.core.category import CategoryCollection
from easydiffraction.core.category import CategoryItem
from easydiffraction.core.metadata import CalculatorSupport
from easydiffraction.core.metadata import Compatibility
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import RangeValidator
from easydiffraction.core.validation import RegexValidator
from easydiffraction.core.variable import NumericDescriptor
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.datablocks.experiment.categories.data.factory import DataFactory
from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
from easydiffraction.datablocks.experiment.item.enums import CalculatorEnum
from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum
from easydiffraction.io.cif.handler import CifHandler
from easydiffraction.utils.logging import log
from easydiffraction.utils.utils import sin_theta_over_lambda_to_d_spacing


class Refln(CategoryItem):
    """Single reflection for single-crystal diffraction data."""

    def __init__(self) -> None:
        super().__init__()

        self._id = StringDescriptor(
            name='id',
            description='Identifier of the reflection',
            value_spec=AttributeSpec(
                default='0',
                # TODO: the following pattern is valid for dict key
                #  (keywords are not checked). CIF label is less strict.
                #  Do we need conversion between CIF and internal label?
                validator=RegexValidator(pattern=r'^[A-Za-z0-9_]*$'),
            ),
            cif_handler=CifHandler(names=['_refln.id']),
        )
        self._d_spacing = NumericDescriptor(
            name='d_spacing',
            description='Distance between lattice planes for this reflection',
            units='Å',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(ge=0),
            ),
            cif_handler=CifHandler(names=['_refln.d_spacing']),
        )
        self._sin_theta_over_lambda = NumericDescriptor(
            name='sin_theta_over_lambda',
            description='The sin(θ)/λ value for this reflection',
            units='Å⁻¹',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(ge=0),
            ),
            cif_handler=CifHandler(names=['_refln.sin_theta_over_lambda']),
        )
        self._index_h = NumericDescriptor(
            name='index_h',
            description='Miller index h of a measured reflection',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(names=['_refln.index_h']),
        )
        self._index_k = NumericDescriptor(
            name='index_k',
            description='Miller index k of a measured reflection',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(names=['_refln.index_k']),
        )
        self._index_l = NumericDescriptor(
            name='index_l',
            description='Miller index l of a measured reflection',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(names=['_refln.index_l']),
        )
        self._intensity_meas = NumericDescriptor(
            name='intensity_meas',
            description=' The intensity of the reflection derived from the measurements.',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(ge=0),
            ),
            cif_handler=CifHandler(names=['_refln.intensity_meas']),
        )
        self._intensity_meas_su = NumericDescriptor(
            name='intensity_meas_su',
            description='Standard uncertainty of the measured intensity.',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(ge=0),
            ),
            cif_handler=CifHandler(names=['_refln.intensity_meas_su']),
        )
        self._intensity_calc = NumericDescriptor(
            name='intensity_calc',
            description='Intensity of the reflection calculated from atom site data',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(ge=0),
            ),
            cif_handler=CifHandler(names=['_refln.intensity_calc']),
        )
        self._wavelength = NumericDescriptor(
            name='wavelength',
            description='Mean wavelength of radiation for this reflection',
            units='Å',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(ge=0),
            ),
            cif_handler=CifHandler(names=['_refln.wavelength']),
        )

        self._identity.category_code = 'refln'
        self._identity.category_entry_name = lambda: str(self.id.value)

    # ------------------------------------------------------------------
    #  Public properties
    # ------------------------------------------------------------------

    @property
    def id(self) -> StringDescriptor:
        """
        Identifier of the reflection.

        Reading this property returns the underlying
        ``StringDescriptor`` object.
        """
        return self._id

    @property
    def d_spacing(self) -> NumericDescriptor:
        """
        Distance between lattice planes for this reflection (Å).

        Reading this property returns the underlying
        ``NumericDescriptor`` object.
        """
        return self._d_spacing

    @property
    def sin_theta_over_lambda(self) -> NumericDescriptor:
        """
        The sin(θ)/λ value for this reflection (Å⁻¹).

        Reading this property returns the underlying
        ``NumericDescriptor`` object.
        """
        return self._sin_theta_over_lambda

    @property
    def index_h(self) -> NumericDescriptor:
        """
        Miller index h of a measured reflection.

        Reading this property returns the underlying
        ``NumericDescriptor`` object.
        """
        return self._index_h

    @property
    def index_k(self) -> NumericDescriptor:
        """
        Miller index k of a measured reflection.

        Reading this property returns the underlying
        ``NumericDescriptor`` object.
        """
        return self._index_k

    @property
    def index_l(self) -> NumericDescriptor:
        """
        Miller index l of a measured reflection.

        Reading this property returns the underlying
        ``NumericDescriptor`` object.
        """
        return self._index_l

    @property
    def intensity_meas(self) -> NumericDescriptor:
        """
        The intensity of the reflection derived from the measurements.

        Reading this property returns the underlying
        ``NumericDescriptor`` object.
        """
        return self._intensity_meas

    @property
    def intensity_meas_su(self) -> NumericDescriptor:
        """
        Standard uncertainty of the measured intensity.

        Reading this property returns the underlying
        ``NumericDescriptor`` object.
        """
        return self._intensity_meas_su

    @property
    def intensity_calc(self) -> NumericDescriptor:
        """
        Intensity of the reflection calculated from atom site data.

        Reading this property returns the underlying
        ``NumericDescriptor`` object.
        """
        return self._intensity_calc

    @property
    def wavelength(self) -> NumericDescriptor:
        """
        Mean wavelength of radiation for this reflection (Å).

        Reading this property returns the underlying
        ``NumericDescriptor`` object.
        """
        return self._wavelength


@DataFactory.register
class ReflnData(CategoryCollection):
    """Collection of reflections for single crystal diffraction data."""

    type_info = TypeInfo(tag='bragg-sc', description='Bragg single-crystal reflection data')
    compatibility = Compatibility(
        sample_form=frozenset({SampleFormEnum.SINGLE_CRYSTAL}),
        scattering_type=frozenset({ScatteringTypeEnum.BRAGG}),
        beam_mode=frozenset({BeamModeEnum.CONSTANT_WAVELENGTH, BeamModeEnum.TIME_OF_FLIGHT}),
    )
    calculator_support = CalculatorSupport(
        calculators=frozenset({CalculatorEnum.CRYSPY}),
    )

    _update_priority = 100

    def __init__(self) -> None:
        super().__init__(item_type=Refln)

    #################
    # Private methods
    #################

    # Should be set only once

    def _create_items_set_hkl_and_id(
        self,
        indices_h: object,
        indices_k: object,
        indices_l: object,
    ) -> None:
        """Set Miller indices."""
        # TODO: split into multiple methods

        # Create items
        self._items = [self._item_type() for _ in range(indices_h.size)]

        # Set indices
        for item, index_h, index_k, index_l in zip(
            self._items, indices_h, indices_k, indices_l, strict=True
        ):
            item.index_h._value = index_h
            item.index_k._value = index_k
            item.index_l._value = index_l

        # Set reflection IDs
        self._set_id([str(i + 1) for i in range(indices_h.size)])

    def _set_id(self, values: object) -> None:
        """Set reflection IDs."""
        for p, v in zip(self._items, values, strict=True):
            p.id._value = v

    def _set_intensity_meas(self, values: object) -> None:
        """Set measured intensity."""
        for p, v in zip(self._items, values, strict=True):
            p.intensity_meas._value = v

    def _set_intensity_meas_su(self, values: object) -> None:
        """Set standard uncertainty of measured intensity values."""
        for p, v in zip(self._items, values, strict=True):
            p.intensity_meas_su._value = v

    def _set_wavelength(self, values: object) -> None:
        """Set wavelength."""
        for p, v in zip(self._items, values, strict=True):
            p.wavelength._value = v

    # Can be set multiple times

    def _set_d_spacing(self, values: object) -> None:
        """Set d-spacing values."""
        for p, v in zip(self._items, values, strict=True):
            p.d_spacing._value = v

    def _set_sin_theta_over_lambda(self, values: object) -> None:
        """Set sin(theta)/lambda values."""
        for p, v in zip(self._items, values, strict=True):
            p.sin_theta_over_lambda._value = v

    def _set_intensity_calc(self, values: object) -> None:
        """Set calculated intensity."""
        for p, v in zip(self._items, values, strict=True):
            p.intensity_calc._value = v

    # Misc

    def _update(self, called_by_minimizer: bool = False) -> None:
        experiment = self._parent
        experiments = experiment._parent
        project = experiments._parent
        structures = project.structures
        calculator = experiment.calculator

        linked_crystal = experiment.linked_crystal
        linked_crystal_id = experiment.linked_crystal.id.value

        if linked_crystal_id not in structures.names:
            log.error(
                f"Linked crystal ID '{linked_crystal_id}' not found in "
                f'structure IDs {structures.names}.'
            )
            return

        structure_id = linked_crystal_id
        structure_scale = linked_crystal.scale.value
        structure = structures[structure_id]

        stol, raw_calc = calculator.calculate_structure_factors(
            structure,
            experiment,
            called_by_minimizer=called_by_minimizer,
        )

        d_spacing = sin_theta_over_lambda_to_d_spacing(stol)
        calc = structure_scale * raw_calc

        self._set_d_spacing(d_spacing)
        self._set_sin_theta_over_lambda(stol)
        self._set_intensity_calc(calc)

    # ------------------------------------------------------------------
    #  Public properties
    # ------------------------------------------------------------------

    @property
    def d_spacing(self) -> np.ndarray:
        """D-spacing values for all reflection data points."""
        return np.fromiter(
            (p.d_spacing.value for p in self._items),
            dtype=float,
        )

    @property
    def sin_theta_over_lambda(self) -> np.ndarray:
        """sinθ/λ values for all reflection data points."""
        return np.fromiter(
            (p.sin_theta_over_lambda.value for p in self._items),
            dtype=float,
        )

    @property
    def index_h(self) -> np.ndarray:
        """Miller h indices for all reflection data points."""
        return np.fromiter(
            (p.index_h.value for p in self._items),
            dtype=float,
        )

    @property
    def index_k(self) -> np.ndarray:
        """Miller k indices for all reflection data points."""
        return np.fromiter(
            (p.index_k.value for p in self._items),
            dtype=float,
        )

    @property
    def index_l(self) -> np.ndarray:
        """Miller l indices for all reflection data points."""
        return np.fromiter(
            (p.index_l.value for p in self._items),
            dtype=float,
        )

    @property
    def intensity_meas(self) -> np.ndarray:
        """Measured structure-factor intensities for all reflections."""
        return np.fromiter(
            (p.intensity_meas.value for p in self._items),
            dtype=float,
        )

    @property
    def intensity_meas_su(self) -> np.ndarray:
        """Standard uncertainties of the measured intensities."""
        return np.fromiter(
            (p.intensity_meas_su.value for p in self._items),
            dtype=float,
        )

    @property
    def intensity_calc(self) -> np.ndarray:
        """Calculated intensities for all reflections."""
        return np.fromiter(
            (p.intensity_calc.value for p in self._items),
            dtype=float,
        )

    @property
    def wavelength(self) -> np.ndarray:
        """Wavelengths associated with each reflection."""
        return np.fromiter(
            (p.wavelength.value for p in self._items),
            dtype=float,
        )
