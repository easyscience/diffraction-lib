# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Bayesian pair-cache manifest rows."""

from __future__ import annotations

from dataclasses import dataclass

from easydiffraction.analysis.categories.bayesian_pair_caches.factory import (
    BayesianPairCachesFactory,
)
from easydiffraction.core.category import CategoryCollection
from easydiffraction.core.category import CategoryItem
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import RegexValidator
from easydiffraction.core.variable import NumericDescriptor
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.io.cif.handler import CifHandler


def _normalized_parameter_pair(
    param_unique_name_x: str,
    param_unique_name_y: str,
) -> tuple[str, str]:
    """Return a stable ordering for a cached parameter pair."""
    if param_unique_name_x <= param_unique_name_y:
        return param_unique_name_x, param_unique_name_y
    return param_unique_name_y, param_unique_name_x


@dataclass(frozen=True, slots=True)
class BayesianPairCachePaths:
    """HDF5 dataset paths for one persisted pair cache."""

    x_path: str
    y_path: str
    density_path: str
    contour_level_path: str


class BayesianPairCacheItem(CategoryItem):
    """Single persisted Bayesian pair-cache manifest row."""

    _category_code = 'bayesian_pair_cache'
    _category_entry_name = 'id'

    def __init__(self) -> None:
        super().__init__()
        self._param_unique_name_x = StringDescriptor(
            name='param_unique_name_x',
            description='First unique parameter name in the cached pair.',
            value_spec=AttributeSpec(
                default='_',
                validator=RegexValidator(pattern=r'^[A-Za-z_][A-Za-z0-9_.]*$'),
            ),
            cif_handler=CifHandler(names=['_bayesian_pair_cache.param_unique_name_x']),
        )
        self._param_unique_name_y = StringDescriptor(
            name='param_unique_name_y',
            description='Second unique parameter name in the cached pair.',
            value_spec=AttributeSpec(
                default='_',
                validator=RegexValidator(pattern=r'^[A-Za-z_][A-Za-z0-9_.]*$'),
            ),
            cif_handler=CifHandler(names=['_bayesian_pair_cache.param_unique_name_y']),
        )
        self._id = StringDescriptor(
            name='id',
            description='Stable identifier for the cached parameter pair.',
            value_spec=AttributeSpec(
                default='_',
                validator=RegexValidator(pattern=r'^[A-Za-z0-9_.:-]+$'),
            ),
            cif_handler=CifHandler(names=['_bayesian_pair_cache.id']),
        )
        self._x_path = StringDescriptor(
            name='x_path',
            description='HDF5 dataset path for the pair-cache x-grid.',
            value_spec=AttributeSpec(default=''),
            cif_handler=CifHandler(names=['_bayesian_pair_cache.x_path']),
        )
        self._y_path = StringDescriptor(
            name='y_path',
            description='HDF5 dataset path for the pair-cache y-grid.',
            value_spec=AttributeSpec(default=''),
            cif_handler=CifHandler(names=['_bayesian_pair_cache.y_path']),
        )
        self._density_path = StringDescriptor(
            name='density_path',
            description='HDF5 dataset path for the pair-cache density grid.',
            value_spec=AttributeSpec(default=''),
            cif_handler=CifHandler(names=['_bayesian_pair_cache.density_path']),
        )
        self._contour_level_path = StringDescriptor(
            name='contour_level_path',
            description='HDF5 dataset path for cached contour levels.',
            value_spec=AttributeSpec(default=''),
            cif_handler=CifHandler(names=['_bayesian_pair_cache.contour_level_path']),
        )
        self._n_grid_x = NumericDescriptor(
            name='n_grid_x',
            description='Number of x-grid points in the cached pair.',
            value_spec=AttributeSpec(default=0),
            cif_handler=CifHandler(names=['_bayesian_pair_cache.n_grid_x']),
        )
        self._n_grid_y = NumericDescriptor(
            name='n_grid_y',
            description='Number of y-grid points in the cached pair.',
            value_spec=AttributeSpec(default=0),
            cif_handler=CifHandler(names=['_bayesian_pair_cache.n_grid_y']),
        )
        self._n_draws_cached = NumericDescriptor(
            name='n_draws_cached',
            description='Number of draws summarized into the cached pair.',
            value_spec=AttributeSpec(default=0),
            cif_handler=CifHandler(names=['_bayesian_pair_cache.n_draws_cached']),
        )

    @property
    def param_unique_name_x(self) -> StringDescriptor:
        """First unique parameter name in the cached pair."""
        return self._param_unique_name_x

    def _set_param_unique_name_x(self, value: str) -> None:
        """Set the first unique parameter name for internal callers."""
        self._param_unique_name_x.value = value

    @property
    def param_unique_name_y(self) -> StringDescriptor:
        """Second unique parameter name in the cached pair."""
        return self._param_unique_name_y

    def _set_param_unique_name_y(self, value: str) -> None:
        """Set the second unique parameter name for internal callers."""
        self._param_unique_name_y.value = value

    @property
    def id(self) -> StringDescriptor:
        """Stable identifier for the cached parameter pair."""
        return self._id

    def _set_id(self, value: str) -> None:
        """Set the pair-cache id for internal callers."""
        self._id.value = value

    @property
    def x_path(self) -> StringDescriptor:
        """HDF5 dataset path for the pair-cache x-grid."""
        return self._x_path

    def _set_x_path(self, value: str) -> None:
        """Set the pair-cache x-grid path for internal callers."""
        self._x_path.value = value

    @property
    def y_path(self) -> StringDescriptor:
        """HDF5 dataset path for the pair-cache y-grid."""
        return self._y_path

    def _set_y_path(self, value: str) -> None:
        """Set the pair-cache y-grid path for internal callers."""
        self._y_path.value = value

    @property
    def density_path(self) -> StringDescriptor:
        """HDF5 dataset path for the pair-cache density grid."""
        return self._density_path

    def _set_density_path(self, value: str) -> None:
        """Set the pair-cache density path for internal callers."""
        self._density_path.value = value

    @property
    def contour_level_path(self) -> StringDescriptor:
        """HDF5 dataset path for cached contour levels."""
        return self._contour_level_path

    def _set_contour_level_path(self, value: str) -> None:
        """Set the contour-level path for internal callers."""
        self._contour_level_path.value = value

    @property
    def n_grid_x(self) -> NumericDescriptor:
        """Number of x-grid points in the cached pair."""
        return self._n_grid_x

    def _set_n_grid_x(self, value: float) -> None:
        """Set the x-grid size for internal callers."""
        self._n_grid_x.value = value

    @property
    def n_grid_y(self) -> NumericDescriptor:
        """Number of y-grid points in the cached pair."""
        return self._n_grid_y

    def _set_n_grid_y(self, value: float) -> None:
        """Set the y-grid size for internal callers."""
        self._n_grid_y.value = value

    @property
    def n_draws_cached(self) -> NumericDescriptor:
        """Number of draws summarized into the cached pair."""
        return self._n_draws_cached

    def _set_n_draws_cached(self, value: float) -> None:
        """Set the cached-draw count for internal callers."""
        self._n_draws_cached.value = value


@BayesianPairCachesFactory.register
class BayesianPairCaches(CategoryCollection):
    """Collection of persisted Bayesian pair-cache manifests."""

    type_info = TypeInfo(
        tag='default',
        description='Persisted Bayesian pair-cache manifests',
    )

    def __init__(self) -> None:
        super().__init__(item_type=BayesianPairCacheItem)

    def create(
        self,
        *,
        parameter_names: tuple[str, str],
        paths: BayesianPairCachePaths,
        grid_shape: tuple[float, float],
        n_draws_cached: float,
        id: str | None = None,
    ) -> None:
        """
        Create a persisted Bayesian pair-cache manifest row.

        Parameters
        ----------
        parameter_names : tuple[str, str]
            Unique parameter names for the cached pair.
        paths : BayesianPairCachePaths
            HDF5 dataset paths for the cached pair payloads.
        grid_shape : tuple[float, float]
            Number of x-grid and y-grid points in the cached pair.
        n_draws_cached : float
            Number of draws summarized into the cached pair.
        id : str | None, default=None
            Explicit persisted row id. When omitted, a simple sequential
            identifier is generated.
        """
        param_unique_name_x, param_unique_name_y = parameter_names
        normalized_x, normalized_y = _normalized_parameter_pair(
            param_unique_name_x,
            param_unique_name_y,
        )
        n_grid_x, n_grid_y = grid_shape
        item = BayesianPairCacheItem()
        item._set_param_unique_name_x(normalized_x)
        item._set_param_unique_name_y(normalized_y)
        item._set_x_path(paths.x_path)
        item._set_y_path(paths.y_path)
        item._set_density_path(paths.density_path)
        item._set_contour_level_path(paths.contour_level_path)
        item._set_n_grid_x(n_grid_x)
        item._set_n_grid_y(n_grid_y)
        item._set_n_draws_cached(n_draws_cached)
        resolved_id = id or str(len(self) + 1)
        item._set_id(resolved_id)
        self.add(item)
