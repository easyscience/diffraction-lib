# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Shared fixtures for functional (API-behaviour) tests."""

from __future__ import annotations

import tempfile

import pytest

TEMP_DIR = tempfile.gettempdir()


@pytest.fixture
def project(tmp_path):
    """Create a minimal unsaved Project for functional tests."""
    from easydiffraction import Project  # noqa: PLC0415

    return Project(name='func_test')


@pytest.fixture
def saved_project(tmp_path):
    """Create a minimal Project saved to a temp directory."""
    from easydiffraction import Project  # noqa: PLC0415

    project = Project(name='func_test')
    project.save_as(str(tmp_path / 'func_project'))
    return project
