# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Shared fixtures and configuration for the whole test suite.

Defines the documented numeric-tolerance convention (one intra-engine
``rtol``/``atol`` pair and one looser cross-engine pair) and a
deterministic ``hypothesis`` profile, so property-based tests never flake
or depend on test ordering (see AGENTS.md testing rules and the
[Testing Guide](../docs/dev/testing-guide.md)).
"""

from __future__ import annotations

import pytest
from hypothesis import HealthCheck
from hypothesis import settings

# Deterministic hypothesis profile: reproducible behaviour, no committed
# example database, no per-example deadline (engine-free property tests can
# still be a touch slow under coverage).
settings.register_profile(
    'easydiffraction',
    derandomize=True,
    database=None,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
settings.load_profile('easydiffraction')

# Numeric-tolerance convention. Prefer these over ad-hoc per-test values.
# Intra-engine: a value against an expected scalar from the same engine.
# Cross-engine: patterns/parameters compared between calculation engines.
INTRA_ENGINE_RTOL = 1e-6
INTRA_ENGINE_ATOL = 1e-8
CROSS_ENGINE_RTOL = 1e-3
CROSS_ENGINE_ATOL = 1e-5


@pytest.fixture
def intra_engine_tol() -> dict[str, float]:
    """Return the documented intra-engine ``rtol``/``atol`` pair."""
    return {'rtol': INTRA_ENGINE_RTOL, 'atol': INTRA_ENGINE_ATOL}


@pytest.fixture
def cross_engine_tol() -> dict[str, float]:
    """Return the documented (looser) cross-engine ``rtol``/``atol`` pair."""
    return {'rtol': CROSS_ENGINE_RTOL, 'atol': CROSS_ENGINE_ATOL}


@pytest.fixture
def seeded_rng():
    """Return a NumPy generator with a fixed seed for reproducible tests."""
    import numpy as np

    return np.random.default_rng(12345)
