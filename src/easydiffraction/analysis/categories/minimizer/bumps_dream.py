# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Persisted category for the BUMPS DREAM minimizer."""

from __future__ import annotations

from typing import ClassVar

from easydiffraction.analysis.categories.minimizer.bayesian_base import BayesianMinimizerBase
from easydiffraction.analysis.categories.minimizer.factory import MinimizerCategoryFactory
from easydiffraction.analysis.minimizers.enums import MinimizerTypeEnum
from easydiffraction.core.metadata import TypeInfo

DEFAULT_SAMPLING_STEPS = 3000
DEFAULT_BURN_IN_STEPS = 600
DEFAULT_THINNING_INTERVAL = 1
DEFAULT_POPULATION_SIZE = 4
DEFAULT_PARALLEL_WORKERS = 0


@MinimizerCategoryFactory.register
class BumpsDreamMinimizer(BayesianMinimizerBase):
    """Persisted settings and results for the BUMPS DREAM minimizer."""

    _engine_metadata: ClassVar[dict[str, str]] = {
        'optimizer_name': 'bumps (dream)',
        'method_name': 'dream',
    }

    type_info = TypeInfo(
        tag=MinimizerTypeEnum.BUMPS_DREAM,
        description='BUMPS library with DREAM Bayesian sampling',
    )

    def __init__(self) -> None:
        super().__init__()
        self._sampling_steps = self._sampling_steps_descriptor(DEFAULT_SAMPLING_STEPS)
        self._burn_in_steps = self._burn_in_steps_descriptor(DEFAULT_BURN_IN_STEPS)
        self._thinning_interval = self._thinning_interval_descriptor(DEFAULT_THINNING_INTERVAL)
        self._population_size = self._population_size_descriptor(DEFAULT_POPULATION_SIZE)
        self._parallel_workers = self._parallel_workers_descriptor(DEFAULT_PARALLEL_WORKERS)
        self._initialization_method = self._initialization_method_descriptor()
        self._random_seed = self._random_seed_descriptor()
        self._runtime_seconds = self._runtime_seconds_descriptor()
        self._point_estimate_name = self._point_estimate_name_descriptor()
        self._sampler_completed = self._sampler_completed_descriptor()
        self._credible_interval_inner = self._credible_interval_inner_descriptor()
        self._credible_interval_outer = self._credible_interval_outer_descriptor()
        self._acceptance_rate_mean = self._acceptance_rate_mean_descriptor()
        self._gelman_rubin_max = self._gelman_rubin_max_descriptor()
        self._effective_sample_size_min = self._effective_sample_size_min_descriptor()
        self._best_log_posterior = self._best_log_posterior_descriptor()
