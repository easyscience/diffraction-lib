# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Shared defaults for the emcee minimizer."""

from __future__ import annotations

import numpy as np

from easydiffraction.analysis.minimizers.enums import InitializationMethodEnum

DEFAULT_METHOD = 'de'
DEFAULT_NSTEPS = 5000
DEFAULT_NBURN = 1000
DEFAULT_THIN = 1
DEFAULT_NWALKERS = 32
DEFAULT_PARALLEL_WORKERS = 0
DEFAULT_INITIALIZATION_METHOD = InitializationMethodEnum.BALL
DEFAULT_PROPOSAL_MOVES = 'de'
MAX_RANDOM_SEED = int(np.iinfo(np.uint32).max)
SUPPORTED_PROPOSAL_MOVES = ('stretch', 'de', 'de_snooker', 'walk')
SUPPORTED_INITIALIZATION_METHODS = (
    InitializationMethodEnum.BALL,
    InitializationMethodEnum.UNIFORM,
    InitializationMethodEnum.PRIOR,
)
SUPPORTED_INITIALIZATION_METHOD_SET = frozenset(SUPPORTED_INITIALIZATION_METHODS)
