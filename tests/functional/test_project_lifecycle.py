# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Functional tests for Project lifecycle: create, save, load."""

from __future__ import annotations

import pytest

from easydiffraction import Project


class TestProjectCreate:
    def test_create_default_project(self):
        Project._loading = True
        try:
            project = Project()
        finally:
            Project._loading = False
        assert project.name == 'untitled_project'

    def test_create_named_project(self):
        Project._loading = True
        try:
            project = Project(name='my_project')
        finally:
            Project._loading = False
        assert project.name == 'my_project'

    def test_project_has_empty_structures(self):
        Project._loading = True
        try:
            project = Project()
        finally:
            Project._loading = False
        assert len(project.structures) == 0

    def test_project_has_empty_experiments(self):
        Project._loading = True
        try:
            project = Project()
        finally:
            Project._loading = False
        assert len(project.experiments) == 0

    def test_project_has_analysis(self):
        Project._loading = True
        try:
            project = Project()
        finally:
            Project._loading = False
        assert project.analysis is not None


class TestProjectSaveLoad:
    def test_save_creates_directory_structure(self, tmp_path):
        Project._loading = True
        try:
            project = Project(name='test')
        finally:
            Project._loading = False
        project.save_as(str(tmp_path / 'proj'))

        assert (tmp_path / 'proj' / 'project.cif').is_file()
        assert (tmp_path / 'proj' / 'structures').is_dir()
        assert (tmp_path / 'proj' / 'experiments').is_dir()
        assert (tmp_path / 'proj' / 'analysis').is_dir()

    def test_save_and_load_preserves_name(self, tmp_path):
        Project._loading = True
        try:
            project = Project(name='round_trip')
        finally:
            Project._loading = False
        project.save_as(str(tmp_path / 'proj'))

        loaded = Project.load(str(tmp_path / 'proj'))
        assert loaded.name == 'round_trip'

    def test_load_nonexistent_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            Project.load(str(tmp_path / 'nonexistent'))


class TestProjectVerbosity:
    def test_default_verbosity_is_full(self):
        Project._loading = True
        try:
            project = Project()
        finally:
            Project._loading = False
        assert project.verbosity.fit.value == 'full'

    def test_set_verbosity_short(self):
        Project._loading = True
        try:
            project = Project()
        finally:
            Project._loading = False
        project.verbosity = 'short'
        assert project.verbosity.fit.value == 'short'

    def test_set_verbosity_silent(self):
        Project._loading = True
        try:
            project = Project()
        finally:
            Project._loading = False
        project.verbosity = 'silent'
        assert project.verbosity.fit.value == 'silent'

    def test_invalid_verbosity_raises(self):
        Project._loading = True
        try:
            project = Project()
        finally:
            Project._loading = False
        with pytest.raises(ValueError, match='invalid'):
            project.verbosity = 'invalid'
