# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Shared fixtures for the unit-test suite.

Unit tests must be hermetic and order-independent (see AGENTS.md testing
rules). A few pieces of process-global state are easy to mutate and hard
to remember to restore -- notably the ``Logger`` error-reaction/mode and
environment variables such as ``EASYDIFFRACTION_ARTIFACT_ROOT``. The
autouse fixture below snapshots that state before every unit test and
restores it afterwards, so one test's mutation can never leak into a
later test regardless of collection (or randomised) order.
"""

from __future__ import annotations

import os

import pytest

from easydiffraction.utils.logging import Logger


@pytest.fixture(autouse=True)
def _reset_global_state():
    """Restore process-global state mutated by a unit test.

    Snapshots the logger error reaction/mode and the full environment
    before the test and restores them afterwards, neutralising leaks
    that would otherwise cause order-dependent failures.
    """
    saved_reaction = Logger._reaction
    saved_mode = Logger._mode
    saved_environ = dict(os.environ)
    try:
        yield
    finally:
        Logger._reaction = saved_reaction
        Logger._mode = saved_mode
        os.environ.clear()
        os.environ.update(saved_environ)
