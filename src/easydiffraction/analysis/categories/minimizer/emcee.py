# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Persisted category for the emcee minimizer."""

from __future__ import annotations

from typing import ClassVar

from easydiffraction.analysis.categories.minimizer.bayesian_base import BayesianMinimizerBase
from easydiffraction.analysis.categories.minimizer.factory import MinimizerCategoryFactory
from easydiffraction.analysis.minimizers.emcee_defaults import DEFAULT_INITIALIZATION_METHOD
from easydiffraction.analysis.minimizers.emcee_defaults import DEFAULT_NBURN as DEFAULT_BURN_IN_STEPS
from easydiffraction.analysis.minimizers.emcee_defaults import DEFAULT_NSTEPS as DEFAULT_SAMPLING_STEPS
from easydiffraction.analysis.minimizers.emcee_defaults import DEFAULT_NWALKERS as DEFAULT_POPULATION_SIZE
from easydiffraction.analysis.minimizers.emcee_defaults import DEFAULT_PARALLEL_WORKERS
from easydiffraction.analysis.minimizers.emcee_defaults import DEFAULT_PROPOSAL_MOVES
from easydiffraction.analysis.minimizers.emcee_defaults import DEFAULT_THIN as DEFAULT_THINNING_INTERVAL
from easydiffraction.analysis.minimizers.emcee_defaults import SUPPORTED_PROPOSAL_MOVES
from easydiffraction.analysis.minimizers.enums import InitializationMethodEnum
from easydiffraction.analysis.minimizers.enums import MinimizerTypeEnum
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import MembershipValidator
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.io.cif.handler import CifHandler

@MinimizerCategoryFactory.register
class EmceeMinimizer(BayesianMinimizerBase):
    """Persisted settings for the emcee minimizer."""

    _engine_metadata: ClassVar[dict[str, str]] = {
        'optimizer_name': 'emcee',
        'method_name': 'de',
    }
    _expected_descriptor_names: ClassVar[tuple[str, ...]] = (
        *BayesianMinimizerBase._expected_descriptor_names,
        'proposal_moves',
    )
    _native_key_map: ClassVar[dict[str, str]] = {
        'sampling_steps': 'nsteps',
        'burn_in_steps': 'nburn',
        'thinning_interval': 'thin',
        'population_size': 'nwalkers',
        'parallel_workers': 'parallel_workers',
        'initialization_method': 'initialization_method',
        'random_seed': 'random_seed',
        'proposal_moves': 'proposal_moves',
    }
    _engine_sync_skip_keys: ClassVar[frozenset[str]] = frozenset({
        'random_seed',
        'parallel_workers',
    })
    _setting_descriptor_names: ClassVar[tuple[str, ...]] = (
        *BayesianMinimizerBase._setting_descriptor_names,
        'proposal_moves',
    )
    _supported_initialization_methods: ClassVar[tuple[InitializationMethodEnum, ...]] = (
        InitializationMethodEnum.BALL,
        InitializationMethodEnum.UNIFORM,
        InitializationMethodEnum.PRIOR,
    )
    type_info = TypeInfo(
        tag=MinimizerTypeEnum.EMCEE,
        description='emcee affine-invariant ensemble Bayesian sampling',
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
        self._proposal_moves = self._proposal_moves_descriptor()

    @classmethod
    def _initialization_method_descriptor(cls) -> StringDescriptor:
        """Create an emcee initialization-method descriptor."""
        allowed = [member.value for member in cls._supported_initialization_methods]
        return StringDescriptor(
            name='initialization_method',
            description='emcee walker initialization method.',
            value_spec=AttributeSpec(
                default=DEFAULT_INITIALIZATION_METHOD.value,
                validator=MembershipValidator(allowed=allowed),
            ),
            cif_handler=CifHandler(names=['_minimizer.initialization_method']),
        )

    @staticmethod
    def _proposal_moves_descriptor() -> StringDescriptor:
        """Create an emcee proposal-moves descriptor."""
        return StringDescriptor(
            name='proposal_moves',
            description='Single emcee proposal move; move mixtures are not persisted in v1.',
            value_spec=AttributeSpec(
                default=DEFAULT_PROPOSAL_MOVES,
                validator=MembershipValidator(allowed=SUPPORTED_PROPOSAL_MOVES),
            ),
            cif_handler=CifHandler(names=['_minimizer.proposal_moves']),
        )

    @property
    def proposal_moves(self) -> StringDescriptor:
        """Single emcee proposal move."""
        return self._proposal_moves

    @proposal_moves.setter
    def proposal_moves(self, value: str) -> None:
        self._proposal_moves.value = value
