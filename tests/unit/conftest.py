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

_STATE_ATTR = '_easydiffraction_saved_global_state'


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item: pytest.Item) -> None:
    """Snapshot process-global state before each unit test."""
    setattr(item, _STATE_ATTR, dict(os.environ))
    Logger._reaction = Logger.Reaction.RAISE
    Logger._mode = Logger.Mode.COMPACT


@pytest.hookimpl(trylast=True)
def pytest_runtest_teardown(item: pytest.Item) -> None:
    """Restore process-global state after each unit test."""
    saved_environ = getattr(item, _STATE_ATTR, None)
    Logger._reaction = Logger.Reaction.RAISE
    Logger._mode = Logger.Mode.COMPACT
    if saved_environ is not None:
        os.environ.clear()
        os.environ.update(saved_environ)
