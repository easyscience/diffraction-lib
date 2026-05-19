# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Bayesian distribution-cache manifest rows."""

from __future__ import annotations

from easydiffraction.analysis.categories.bayesian_distribution_caches.factory import (
    BayesianDistributionCachesFactory,
)
from easydiffraction.core.category import CategoryCollection
from easydiffraction.core.category import CategoryItem
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import RegexValidator
from easydiffraction.core.variable import NumericDescriptor
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.io.cif.handler import CifHandler


class BayesianDistributionCacheItem(CategoryItem):
    """Single persisted Bayesian distribution-cache manifest row."""

    _category_code = 'bayesian_distribution_cache'
    _category_entry_name = 'param_unique_name'

    def __init__(self) -> None:
        super().__init__()
        self._param_unique_name = StringDescriptor(
            name='param_unique_name',
            description='Unique parameter name for the cached distribution.',
            value_spec=AttributeSpec(
                default='_',
                validator=RegexValidator(pattern=r'^[A-Za-z_][A-Za-z0-9_.]*$'),
            ),
            cif_handler=CifHandler(names=['_bayesian_distribution_cache.param_unique_name']),
        )
        self._x_path = StringDescriptor(
            name='x_path',
            description='HDF5 dataset path for the distribution x-grid.',
            value_spec=AttributeSpec(default=''),
            cif_handler=CifHandler(names=['_bayesian_distribution_cache.x_path']),
        )
        self._density_path = StringDescriptor(
            name='density_path',
            description='HDF5 dataset path for the cached density values.',
            value_spec=AttributeSpec(default=''),
            cif_handler=CifHandler(names=['_bayesian_distribution_cache.density_path']),
        )
        self._n_grid = NumericDescriptor(
            name='n_grid',
            description='Number of grid points in the cached distribution.',
            value_spec=AttributeSpec(default=0),
            cif_handler=CifHandler(names=['_bayesian_distribution_cache.n_grid']),
        )
        self._n_draws_cached = NumericDescriptor(
            name='n_draws_cached',
            description='Number of draws summarized into the cached distribution.',
            value_spec=AttributeSpec(default=0),
            cif_handler=CifHandler(names=['_bayesian_distribution_cache.n_draws_cached']),
        )

    @property
    def param_unique_name(self) -> StringDescriptor:
        """Unique parameter name for the cached distribution."""
        return self._param_unique_name

    def _set_param_unique_name(self, value: str) -> None:
        """Set the unique parameter name for internal callers."""
        self._param_unique_name.value = value

    @property
    def x_path(self) -> StringDescriptor:
        """HDF5 dataset path for the distribution x-grid."""
        return self._x_path

    def _set_x_path(self, value: str) -> None:
        """Set the x-grid dataset path for internal callers."""
        self._x_path.value = value

    @property
    def density_path(self) -> StringDescriptor:
        """HDF5 dataset path for the cached density values."""
        return self._density_path

    def _set_density_path(self, value: str) -> None:
        """Set the density dataset path for internal callers."""
        self._density_path.value = value

    @property
    def n_grid(self) -> NumericDescriptor:
        """Number of grid points in the cached distribution."""
        return self._n_grid

    def _set_n_grid(self, value: float) -> None:
        """Set the grid-size count for internal callers."""
        self._n_grid.value = value

    @property
    def n_draws_cached(self) -> NumericDescriptor:
        """Number of draws summarized into the cached distribution."""
        return self._n_draws_cached

    def _set_n_draws_cached(self, value: float) -> None:
        """Set the cached-draw count for internal callers."""
        self._n_draws_cached.value = value


@BayesianDistributionCachesFactory.register
class BayesianDistributionCaches(CategoryCollection):
    """Collection of persisted Bayesian distribution-cache manifests."""

    type_info = TypeInfo(
        tag='default',
        description='Persisted Bayesian distribution-cache manifests',
    )

    def __init__(self) -> None:
        super().__init__(item_type=BayesianDistributionCacheItem)

    def create(
        self,
        *,
        param_unique_name: str,
        x_path: str,
        density_path: str,
        n_grid: float,
        n_draws_cached: float,
    ) -> None:
        """
        Create a persisted Bayesian distribution-cache manifest row.

        Parameters
        ----------
        param_unique_name : str
            Unique parameter name for the cached distribution.
        x_path : str
            HDF5 dataset path for the distribution x-grid.
        density_path : str
            HDF5 dataset path for the cached density values.
        n_grid : float
            Number of grid points in the cached distribution.
        n_draws_cached : float
            Number of draws summarized into the cached distribution.
        """
        item = BayesianDistributionCacheItem()
        item._set_param_unique_name(param_unique_name)
        item._set_x_path(x_path)
        item._set_density_path(density_path)
        item._set_n_grid(n_grid)
        item._set_n_draws_cached(n_draws_cached)
        self.add(item)
