# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Bayesian predictive-dataset manifest rows."""

from __future__ import annotations

from dataclasses import dataclass

from easydiffraction.analysis.categories.bayesian_predictive_datasets.factory import (
    BayesianPredictiveDatasetsFactory,
)
from easydiffraction.core.category import CategoryCollection
from easydiffraction.core.category import CategoryItem
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.variable import NumericDescriptor
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.io.cif.handler import CifHandler


@dataclass(frozen=True, slots=True)
class BayesianPredictiveDatasetPaths:
    """HDF5 dataset paths for one predictive dataset."""

    x_path: str
    best_sample_prediction_path: str
    lower_95_path: str | None = None
    upper_95_path: str | None = None
    lower_68_path: str | None = None
    upper_68_path: str | None = None
    draws_path: str | None = None


class BayesianPredictiveDatasetItem(CategoryItem):
    """Single persisted Bayesian predictive-dataset manifest row."""

    _category_code = 'bayesian_predictive_dataset'
    _category_entry_name = 'experiment_name'

    def __init__(self) -> None:
        super().__init__()
        self._experiment_name = StringDescriptor(
            name='experiment_name',
            description='Experiment name for the cached predictive dataset.',
            value_spec=AttributeSpec(default=''),
            cif_handler=CifHandler(names=['_bayesian_predictive_dataset.experiment_name']),
        )
        self._x_axis_name = StringDescriptor(
            name='x_axis_name',
            description='Name of the predictive dataset x-axis.',
            value_spec=AttributeSpec(default=''),
            cif_handler=CifHandler(names=['_bayesian_predictive_dataset.x_axis_name']),
        )
        self._x_path = StringDescriptor(
            name='x_path',
            description='HDF5 dataset path for the predictive x-axis values.',
            value_spec=AttributeSpec(default=''),
            cif_handler=CifHandler(names=['_bayesian_predictive_dataset.x_path']),
        )
        self._best_sample_prediction_path = StringDescriptor(
            name='best_sample_prediction_path',
            description='HDF5 dataset path for the committed predictive curve.',
            value_spec=AttributeSpec(default=''),
            cif_handler=CifHandler(
                names=['_bayesian_predictive_dataset.best_sample_prediction_path']
            ),
        )
        self._lower_95_path = StringDescriptor(
            name='lower_95_path',
            description='HDF5 dataset path for the lower 95% predictive band.',
            value_spec=AttributeSpec(default=None, allow_none=True),
            cif_handler=CifHandler(names=['_bayesian_predictive_dataset.lower_95_path']),
        )
        self._upper_95_path = StringDescriptor(
            name='upper_95_path',
            description='HDF5 dataset path for the upper 95% predictive band.',
            value_spec=AttributeSpec(default=None, allow_none=True),
            cif_handler=CifHandler(names=['_bayesian_predictive_dataset.upper_95_path']),
        )
        self._lower_68_path = StringDescriptor(
            name='lower_68_path',
            description='HDF5 dataset path for the lower 68% predictive band.',
            value_spec=AttributeSpec(default=None, allow_none=True),
            cif_handler=CifHandler(names=['_bayesian_predictive_dataset.lower_68_path']),
        )
        self._upper_68_path = StringDescriptor(
            name='upper_68_path',
            description='HDF5 dataset path for the upper 68% predictive band.',
            value_spec=AttributeSpec(default=None, allow_none=True),
            cif_handler=CifHandler(names=['_bayesian_predictive_dataset.upper_68_path']),
        )
        self._draws_path = StringDescriptor(
            name='draws_path',
            description='HDF5 dataset path for cached predictive draws.',
            value_spec=AttributeSpec(default=None, allow_none=True),
            cif_handler=CifHandler(names=['_bayesian_predictive_dataset.draws_path']),
        )
        self._n_x = NumericDescriptor(
            name='n_x',
            description='Number of x-axis points in the cached predictive dataset.',
            value_spec=AttributeSpec(default=0),
            cif_handler=CifHandler(names=['_bayesian_predictive_dataset.n_x']),
        )
        self._n_draws_cached = NumericDescriptor(
            name='n_draws_cached',
            description='Number of cached predictive draws.',
            value_spec=AttributeSpec(default=0),
            cif_handler=CifHandler(names=['_bayesian_predictive_dataset.n_draws_cached']),
        )

    @property
    def experiment_name(self) -> StringDescriptor:
        """Experiment name for the cached predictive dataset."""
        return self._experiment_name

    def _set_experiment_name(self, value: str) -> None:
        """Set the experiment name for internal callers."""
        self._experiment_name.value = value

    @property
    def x_axis_name(self) -> StringDescriptor:
        """Name of the predictive dataset x-axis."""
        return self._x_axis_name

    def _set_x_axis_name(self, value: str) -> None:
        """Set the x-axis name for internal callers."""
        self._x_axis_name.value = value

    @property
    def x_path(self) -> StringDescriptor:
        """HDF5 dataset path for the predictive x-axis values."""
        return self._x_path

    def _set_x_path(self, value: str) -> None:
        """Set the predictive x-axis path for internal callers."""
        self._x_path.value = value

    @property
    def best_sample_prediction_path(self) -> StringDescriptor:
        """HDF5 dataset path for the committed predictive curve."""
        return self._best_sample_prediction_path

    def _set_best_sample_prediction_path(self, value: str) -> None:
        """Set the best-sample prediction path for internal callers."""
        self._best_sample_prediction_path.value = value

    @property
    def lower_95_path(self) -> StringDescriptor:
        """HDF5 dataset path for the lower 95% predictive band."""
        return self._lower_95_path

    def _set_lower_95_path(self, value: str | None) -> None:
        """Set the lower-95 path for internal callers."""
        self._lower_95_path.value = value

    @property
    def upper_95_path(self) -> StringDescriptor:
        """HDF5 dataset path for the upper 95% predictive band."""
        return self._upper_95_path

    def _set_upper_95_path(self, value: str | None) -> None:
        """Set the upper-95 path for internal callers."""
        self._upper_95_path.value = value

    @property
    def lower_68_path(self) -> StringDescriptor:
        """HDF5 dataset path for the lower 68% predictive band."""
        return self._lower_68_path

    def _set_lower_68_path(self, value: str | None) -> None:
        """Set the lower-68 path for internal callers."""
        self._lower_68_path.value = value

    @property
    def upper_68_path(self) -> StringDescriptor:
        """HDF5 dataset path for the upper 68% predictive band."""
        return self._upper_68_path

    def _set_upper_68_path(self, value: str | None) -> None:
        """Set the upper-68 path for internal callers."""
        self._upper_68_path.value = value

    @property
    def draws_path(self) -> StringDescriptor:
        """HDF5 dataset path for cached predictive draws."""
        return self._draws_path

    def _set_draws_path(self, value: str | None) -> None:
        """Set the predictive-draws path for internal callers."""
        self._draws_path.value = value

    @property
    def n_x(self) -> NumericDescriptor:
        """Number of x-axis points in the cached predictive dataset."""
        return self._n_x

    def _set_n_x(self, value: float) -> None:
        """Set the predictive x-axis size for internal callers."""
        self._n_x.value = value

    @property
    def n_draws_cached(self) -> NumericDescriptor:
        """Number of cached predictive draws."""
        return self._n_draws_cached

    def _set_n_draws_cached(self, value: float) -> None:
        """Set the cached predictive-draw count for internal callers."""
        self._n_draws_cached.value = value


@BayesianPredictiveDatasetsFactory.register
class BayesianPredictiveDatasets(CategoryCollection):
    """Collection of persisted Bayesian predictive-dataset manifests."""

    type_info = TypeInfo(
        tag='default',
        description='Persisted Bayesian predictive-dataset manifests',
    )

    def __init__(self) -> None:
        super().__init__(item_type=BayesianPredictiveDatasetItem)

    def create(
        self,
        *,
        experiment_name: str,
        x_axis_name: str,
        paths: BayesianPredictiveDatasetPaths,
        n_x: float,
        n_draws_cached: float,
    ) -> None:
        """
        Create a persisted Bayesian predictive-dataset manifest row.

        Parameters
        ----------
        experiment_name : str
            Experiment name for the cached predictive dataset.
        x_axis_name : str
            Name of the predictive dataset x-axis.
        paths : BayesianPredictiveDatasetPaths
            HDF5 dataset paths for the predictive dataset payloads.
        n_x : float
            Number of x-axis points in the cached predictive dataset.
        n_draws_cached : float
            Number of cached predictive draws.
        """
        item = BayesianPredictiveDatasetItem()
        item._set_experiment_name(experiment_name)
        item._set_x_axis_name(x_axis_name)
        item._set_x_path(paths.x_path)
        item._set_best_sample_prediction_path(paths.best_sample_prediction_path)
        item._set_lower_95_path(paths.lower_95_path)
        item._set_upper_95_path(paths.upper_95_path)
        item._set_lower_68_path(paths.lower_68_path)
        item._set_upper_68_path(paths.upper_68_path)
        item._set_draws_path(paths.draws_path)
        item._set_n_x(n_x)
        item._set_n_draws_cached(n_draws_cached)
        self.add(item)
