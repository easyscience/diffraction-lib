# SPDX-FileCopyrightText: 2021-2026 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import numpy as np

from easydiffraction.core.category import CategoryCollection
from easydiffraction.core.category import CategoryItem
from easydiffraction.core.parameters import NumericDescriptor
from easydiffraction.core.parameters import StringDescriptor
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import DataTypes
from easydiffraction.core.validation import RangeValidator
from easydiffraction.core.validation import RegexValidator
from easydiffraction.io.cif.handler import CifHandler


class Refln(CategoryItem):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # TODO: Rename to _refln.id following coreCIF
        self._refln_id = StringDescriptor(
            name='refln_id',
            description='Identifier for this...',
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
                    '_refln.refln_id',
                ]
            ),
        )
        self._d_spacing = NumericDescriptor(
            name='d_spacing',
            description='The distance between lattice planes in the crystal for this reflection.',
            value_spec=AttributeSpec(
                type_=DataTypes.NUMERIC,
                default=0.0,
                content_validator=RangeValidator(ge=0),
            ),
            units='Å',
            cif_handler=CifHandler(
                names=[
                    '_refln.d_spacing',
                ]
            ),
        )
        self._sin_theta_over_lambda = NumericDescriptor(
            name='sin_theta_over_lambda',
            description='The sin(θ)/λ value for this reflection.',
            value_spec=AttributeSpec(
                type_=DataTypes.NUMERIC,
                default=0.0,
                content_validator=RangeValidator(ge=0),
            ),
            units='Å⁻¹',
            cif_handler=CifHandler(
                names=[
                    '_refln.sin_theta_over_lambda',
                ]
            ),
        )
        self._index_h = NumericDescriptor(
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
        self._index_k = NumericDescriptor(
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
        self._index_l = NumericDescriptor(
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
        self._intensity_calc = NumericDescriptor(
            name='intensity_calc',
            description='...',
            value_spec=AttributeSpec(
                type_=DataTypes.NUMERIC,
                default=0.0,
                content_validator=RangeValidator(ge=0),
            ),
            cif_handler=CifHandler(
                names=[
                    '_refln.intensity_calc',
                ]
            ),
        )

        self._identity.category_code = 'refln'
        self._identity.category_entry_name = lambda: str(self.refln_id.value)

    @property
    def refln_id(self) -> StringDescriptor:
        return self._refln_id

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


class ReflnData(CategoryCollection):
    """..."""

    _update_priority = 100

    def __init__(self):
        super().__init__(item_type=Refln)

    # Should be set only once

    def _set_hkl(self, indices_h, indices_k, indices_l) -> None:
        """Helper method to set Miller indices."""
        # TODO: split into multiple methods
        # TODO: do we set _items here and reuse them for all other
        #  _set_XXX methods?
        self._items = [self._item_type() for _ in range(indices_h.size)]
        for p, index_h, index_k, index_l in zip(
            self._items, indices_h, indices_k, indices_l, strict=True
        ):
            p.index_h._value = index_h
            p.index_k._value = index_k
            p.index_l._value = index_l
        self._set_refln_id([str(i + 1) for i in range(indices_h.size)])

    def _set_refln_id(self, values) -> None:
        """Helper method to set reflection IDs."""
        for p, v in zip(self._items, values, strict=True):
            p.refln_id._value = v

    def _set_meas(self, values) -> None:
        """Helper method to set measured intensity."""
        for p, v in zip(self._items, values, strict=True):
            p.intensity_meas._value = v

    def _set_meas_su(self, values) -> None:
        """Helper method to set standard uncertainty of measured
        intensity.
        """
        for p, v in zip(self._items, values, strict=True):
            p.intensity_meas_su._value = v

    # Can be set multiple times

    def _set_d_spacing(self, values) -> None:
        """Helper method to set d-spacing values."""
        for p, v in zip(self._items, values, strict=True):
            p.d_spacing._value = v

    def _set_sin_theta_over_lambda(self, values) -> None:
        """Helper method to set sin(theta)/lambda values."""
        for p, v in zip(self._items, values, strict=True):
            p.sin_theta_over_lambda._value = v

    def _set_calc(self, values) -> None:
        """Helper method to set calculated intensity."""
        for p, v in zip(self._items, values, strict=True):
            p.intensity_calc._value = v

    @property
    def d(self) -> np.ndarray:
        return np.fromiter((p.d_spacing.value for p in self._items), dtype=float)

    @property
    def stol(self) -> np.ndarray:
        return np.fromiter((p.sin_theta_over_lambda.value for p in self._items), dtype=float)

    @property
    def indices_h(self) -> np.ndarray:
        return np.fromiter((p.index_h.value for p in self._items), dtype=float)

    @property
    def indices_k(self) -> np.ndarray:
        return np.fromiter((p.index_k.value for p in self._items), dtype=float)

    @property
    def indices_l(self) -> np.ndarray:
        return np.fromiter((p.index_l.value for p in self._items), dtype=float)

    @property
    def meas(self) -> np.ndarray:
        return np.fromiter((p.intensity_meas.value for p in self._items), dtype=float)

    @property
    def meas_su(self) -> np.ndarray:
        return np.fromiter((p.intensity_meas_su.value for p in self._items), dtype=float)

    @property
    def calc(self) -> np.ndarray:
        return np.fromiter((p.intensity_calc.value for p in self._items), dtype=float)

    def _update(self, called_by_minimizer=False):
        experiment = self._parent
        experiments = experiment._parent
        project = experiments._parent
        sample_models = project.sample_models
        # calculator = experiment.calculator  # TODO: move from analysis
        calculator = project.analysis.calculator

        initial_calc = np.zeros_like(self.indices_h)
        calc = initial_calc
        linked_crystal = experiment.linked_crystal
        linked_crystal_id = experiment.linked_crystal.id.value
        if linked_crystal_id in sample_models.names:
            sample_model_id = linked_crystal_id
            sample_model_scale = linked_crystal.scale.value
            sample_model = sample_models[sample_model_id]

            stol, sample_model_calc = calculator.calculate_structure_factors(
                sample_model,
                experiment,
                called_by_minimizer=called_by_minimizer,
            )

            calc = sample_model_scale * sample_model_calc

        self._set_sin_theta_over_lambda(stol)
        self._set_d_spacing(0.5 / stol)  # TODO: Move to .utils.utils
        self._set_calc(calc)
