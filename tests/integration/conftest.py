# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Shared pytest configuration for the integration test layer.

Integration tests exercise real calculation engines and downloaded data,
so they belong to the ``pr`` cost tier: they run on pull requests and on
``develop``/``master``, but not on every feature-branch push. Rather than
decorate each integration test individually, they are marked here at
collection time. A test may still opt up to the ``nightly`` tier with
``@pytest.mark.nightly``; such tests are left untouched.

This auto-marking is scoped to ``tests/integration/`` by path, so it does
not affect unit or functional tests collected in the same session.
"""

from __future__ import annotations

import pytest


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Mark every integration test as ``pr`` unless it is ``nightly``.

    ``tryfirst`` ensures this runs before pytest's own ``-m`` deselection,
    so the added marker participates in marker-expression filtering.
    """
    for item in items:
        path = str(getattr(item, 'fspath', '')).replace('\\', '/')
        if '/tests/integration/' not in path:
            continue
        if item.get_closest_marker('nightly'):
            continue
        item.add_marker(pytest.mark.pr)
