# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Functional tests for switchable categories: type getters/setters."""

from __future__ import annotations

import tempfile

from easydiffraction import Project
from easydiffraction import download_data

TEMP_DIR = tempfile.gettempdir()


def _make_project_with_experiment():
    Project._loading = True
    try:
        project = Project()
    finally:
        Project._loading = False

    project.structures.create(name='s')
    data_path = download_data(id=3, destination=TEMP_DIR)
    project.experiments.add_from_data_path(name='e', data_path=data_path)
    return project


# ------------------------------------------------------------------
#  Analysis switchable categories
# ------------------------------------------------------------------


class TestAnalysisSwitchableCategories:
    def test_aliases_default(self):
        project = _make_project_with_experiment()
        assert project.analysis.aliases is not None

    def test_constraints_default(self):
        project = _make_project_with_experiment()
        assert project.analysis.constraints is not None

    def test_fit_mode_default(self):
        project = _make_project_with_experiment()
        assert project.analysis.fit_mode is not None

    def test_minimizer_default(self):
        project = _make_project_with_experiment()
        assert project.analysis.minimizer_type is not None


# ------------------------------------------------------------------
#  Experiment switchable categories
# ------------------------------------------------------------------


class TestExperimentSwitchableCategories:
    def test_background_type_has_getter(self):
        project = _make_project_with_experiment()
        expt = project.experiments['e']
        assert expt.background_type is not None

    def test_calculator_type_has_getter(self):
        project = _make_project_with_experiment()
        expt = project.experiments['e']
        assert expt.calculator_type is not None
