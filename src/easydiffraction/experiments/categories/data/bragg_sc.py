# SPDX-FileCopyrightText: 2021-2026 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import numpy as np

from easydiffraction.core.category import CategoryCollection
from easydiffraction.core.category import CategoryItem
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import RangeValidator
from easydiffraction.core.validation import RegexValidator
from easydiffraction.core.variable import NumericDescriptor
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.io.cif.handler import CifHandler
from easydiffraction.utils.logging import log
from easydiffraction.utils.utils import sin_theta_over_lambda_to_d_spacing


class Refln(CategoryItem):
    """Single reflection for single crystal diffraction data
    category.
    """

    def __init__(self) -> None:
        super().__init__()

        self._id = StringDescriptor(
            name='id',
            description='Identifier of the reflection.',
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
            description='The distance between lattice planes in the crystal for this reflection.',
            units='Å',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(ge=0),
            ),
            cif_handler=CifHandler(names=['_refln.d_spacing']),
        )
        self._sin_theta_over_lambda = NumericDescriptor(
            name='sin_theta_over_lambda',
            description='The sin(θ)/λ value for this reflection.',
            units='Å⁻¹',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(ge=0),
            ),
            cif_handler=CifHandler(names=['_refln.sin_theta_over_lambda']),
        )
        self._index_h = NumericDescriptor(
            name='index_h',
            description='Miller index h of a measured reflection.',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(names=['_refln.index_h']),
        )
        self._index_k = NumericDescriptor(
            name='index_k',
            description='Miller index k of a measured reflection.',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(names=['_refln.index_k']),
        )
        self._index_l = NumericDescriptor(
            name='index_l',
            description='Miller index l of a measured reflection.',
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
            description='The intensity of the reflection calculated from the atom site data.',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(ge=0),
            ),
            cif_handler=CifHandler(names=['_refln.intensity_calc']),
        )
        self._wavelength = NumericDescriptor(
            name='wavelength',
            description='The mean wavelength of radiation used to measure this reflection.',
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
        return self._id

    @property
    def d_spacing(self) -> NumericDescriptor:
        return self._d_spacing

    @property
    def sin_theta_over_lambda(self) -> NumericDescriptor:
        return self._sin_theta_over_lambda

    @property
    def index_h(self) -> NumericDescriptor:
        return self._index_h

    @property
    def index_k(self) -> NumericDescriptor:
        return self._index_k

    @property
    def index_l(self) -> NumericDescriptor:
        return self._index_l

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
    def wavelength(self) -> NumericDescriptor:
        return self._wavelength


class ReflnData(CategoryCollection):
    """Collection of reflections for single crystal diffraction data."""

    _update_priority = 100

    def __init__(self):
        super().__init__(item_type=Refln)

    #################
    # Private methods
    #################

    # Should be set only once

    def _create_items_set_hkl_and_id(self, indices_h, indices_k, indices_l) -> None:
        """Helper method to set Miller indices."""
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

    def _set_id(self, values) -> None:
        """Helper method to set reflection IDs."""
        for p, v in zip(self._items, values, strict=True):
            p.id._value = v

    def _set_intensity_meas(self, values) -> None:
        """Helper method to set measured intensity."""
        for p, v in zip(self._items, values, strict=True):
            p.intensity_meas._value = v

    def _set_intensity_meas_su(self, values) -> None:
        """Helper method to set standard uncertainty of measured
        intensity.
        """
        for p, v in zip(self._items, values, strict=True):
            p.intensity_meas_su._value = v

    def _set_wavelength(self, values) -> None:
        """Helper method to set wavelength."""
        for p, v in zip(self._items, values, strict=True):
            p.wavelength._value = v

    # Can be set multiple times

    def _set_d_spacing(self, values) -> None:
        """Helper method to set d-spacing values."""
        for p, v in zip(self._items, values, strict=True):
            p.d_spacing._value = v

    def _set_sin_theta_over_lambda(self, values) -> None:
        """Helper method to set sin(theta)/lambda values."""
        for p, v in zip(self._items, values, strict=True):
            p.sin_theta_over_lambda._value = v

    def _set_intensity_calc(self, values) -> None:
        """Helper method to set calculated intensity."""
        for p, v in zip(self._items, values, strict=True):
            p.intensity_calc._value = v

    # Misc

    def _update(self, called_by_minimizer=False):
        experiment = self._parent
        experiments = experiment._parent
        project = experiments._parent
        sample_models = project.sample_models
        # calculator = experiment.calculator  # TODO: move from analysis
        calculator = project.analysis.calculator

        linked_crystal = experiment.linked_crystal
        linked_crystal_id = experiment.linked_crystal.id.value

        if linked_crystal_id not in sample_models.names:
            log.error(
                f"Linked crystal ID '{linked_crystal_id}' not found in "
                f'sample model IDs {sample_models.names}.'
            )
            return

        sample_model_id = linked_crystal_id
        sample_model_scale = linked_crystal.scale.value
        sample_model = sample_models[sample_model_id]

        stol, raw_calc = calculator.calculate_structure_factors(
            sample_model,
            experiment,
            called_by_minimizer=called_by_minimizer,
        )

        d_spacing = sin_theta_over_lambda_to_d_spacing(stol)
        calc = sample_model_scale * raw_calc

        self._set_d_spacing(d_spacing)
        self._set_sin_theta_over_lambda(stol)
        self._set_intensity_calc(calc)

    # ------------------------------------------------------------------
    #  Public properties
    # ------------------------------------------------------------------

    @property
    def d_spacing(self) -> np.ndarray:
        return np.fromiter(
            (p.d_spacing.value for p in self._items),
            dtype=float,  # TODO: needed? DataTypes.NUMERIC?
        )

    @property
    def sin_theta_over_lambda(self) -> np.ndarray:
        return np.fromiter(
            (p.sin_theta_over_lambda.value for p in self._items),
            dtype=float,  # TODO: needed? DataTypes.NUMERIC?
        )

    @property
    def index_h(self) -> np.ndarray:
        return np.fromiter(
            (p.index_h.value for p in self._items),
            dtype=float,  # TODO: needed? DataTypes.NUMERIC?
        )

    @property
    def index_k(self) -> np.ndarray:
        return np.fromiter(
            (p.index_k.value for p in self._items),
            dtype=float,  # TODO: needed? DataTypes.NUMERIC?
        )

    @property
    def index_l(self) -> np.ndarray:
        return np.fromiter(
            (p.index_l.value for p in self._items),
            dtype=float,  # TODO: needed? DataTypes.NUMERIC?
        )

    @property
    def intensity_meas(self) -> np.ndarray:
        return np.fromiter(
            (p.intensity_meas.value for p in self._items),
            dtype=float,  # TODO: needed? DataTypes.NUMERIC?
        )

    @property
    def intensity_meas_su(self) -> np.ndarray:
        return np.fromiter(
            (p.intensity_meas_su.value for p in self._items),
            dtype=float,  # TODO: needed? DataTypes.NUMERIC?
        )

    @property
    def intensity_calc(self) -> np.ndarray:
        return np.fromiter(
            (p.intensity_calc.value for p in self._items),
            dtype=float,  # TODO: needed? DataTypes.NUMERIC?
        )

    @property
    def wavelength(self) -> np.ndarray:
        return np.fromiter(
            (p.wavelength.value for p in self._items),
            dtype=float,  # TODO: needed? DataTypes.NUMERIC?
        )
