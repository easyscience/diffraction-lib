# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for load_numeric_block, extract_project_from_zip,
extract_data_paths_from_zip, and extract_data_paths_from_dir."""

from __future__ import annotations

import zipfile
from pathlib import Path

import numpy as np
import pytest

from easydiffraction.io.ascii import extract_data_paths_from_dir
from easydiffraction.io.ascii import extract_data_paths_from_zip
from easydiffraction.io.ascii import extract_project_from_zip
from easydiffraction.io.ascii import load_numeric_block
from easydiffraction.project.project import Project


class TestLoadNumericBlock:
    """Tests for load_numeric_block."""

    def test_plain_numeric_file(self, tmp_path):
        """Parses a file with only numeric rows."""
        f = tmp_path / 'data.dat'
        f.write_text('1 2 3\n4 5 6\n')
        result = load_numeric_block(f)
        assert result.shape == (2, 3)
        np.testing.assert_array_equal(result[0], [1, 2, 3])

    def test_skips_header_lines(self, tmp_path):
        """Non-numeric header lines are skipped."""
        f = tmp_path / 'data.dat'
        f.write_text('# comment\nx y z\n1 2 3\n4 5 6\n')
        result = load_numeric_block(f)
        assert result.shape == (2, 3)

    def test_skips_footer_lines(self, tmp_path):
        """Non-numeric footer lines are skipped."""
        f = tmp_path / 'data.dat'
        f.write_text('1 2 3\n4 5 6\nEND\n')
        result = load_numeric_block(f)
        assert result.shape == (2, 3)

    def test_skips_header_and_footer(self, tmp_path):
        """Both header and footer non-numeric lines are skipped."""
        f = tmp_path / 'data.dat'
        f.write_text('IGOR\nWAVES tof yint yerr nc\nBEGIN\n1 2 3 4\n5 6 7 8\nEND\n')
        result = load_numeric_block(f)
        assert result.shape == (2, 4)
        np.testing.assert_array_equal(result[0], [1, 2, 3, 4])

    def test_skips_blank_lines(self, tmp_path):
        """Blank lines are ignored."""
        f = tmp_path / 'data.dat'
        f.write_text('\n1 2 3\n\n4 5 6\n\n')
        result = load_numeric_block(f)
        assert result.shape == (2, 3)

    def test_raises_on_no_numeric_lines(self, tmp_path):
        """Raises OSError when no numeric data is found."""
        f = tmp_path / 'empty.dat'
        f.write_text('header\nfooter\n')
        with pytest.raises(OSError, match='no numeric lines found'):
            load_numeric_block(f)

    def test_raises_on_empty_file(self, tmp_path):
        """Raises OSError for an empty file."""
        f = tmp_path / 'empty.dat'
        f.write_text('')
        with pytest.raises(OSError, match='no numeric lines found'):
            load_numeric_block(f)


class TestExtractProjectFromZip:
    """Tests for extract_project_from_zip."""

    def test_extracts_project_dir(self, tmp_path):
        """Returns path to the directory containing project.edstar."""
        zip_path = tmp_path / 'proj.zip'
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('my_project/project.edstar', 'data_project\n')
            zf.writestr('my_project/structures/struct.cif', 'data_struct\n')

        result = extract_project_from_zip(zip_path, destination=tmp_path / 'out')

        assert result.endswith('my_project')
        assert (tmp_path / 'out' / 'my_project' / 'project.edstar').is_file()

    def test_extracts_to_temp_dir_by_default(self, tmp_path):
        """Without destination, files go to a temp directory."""
        zip_path = tmp_path / 'proj.zip'
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('myproj/project.edstar', 'data_project\n')

        result = extract_project_from_zip(zip_path)

        assert 'myproj' in result
        assert 'project.edstar' not in result  # returns parent dir, not file

    def test_raises_file_not_found(self, tmp_path):
        """Raises FileNotFoundError for missing ZIP path."""
        with pytest.raises(FileNotFoundError):
            extract_project_from_zip(tmp_path / 'missing.zip')

    def test_raises_value_error_no_project_cif(self, tmp_path):
        """Raises ValueError when ZIP has no project.edstar."""
        zip_path = tmp_path / 'bad.zip'
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('data.dat', '1 2 3\n')

        with pytest.raises(ValueError, match=r'No project\.edstar found'):
            extract_project_from_zip(zip_path)

    def test_destination_creates_directory(self, tmp_path):
        """Destination directory is created if it does not exist."""
        zip_path = tmp_path / 'proj.zip'
        dest = tmp_path / 'nested' / 'output'
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('proj/project.edstar', 'data\n')

        result = extract_project_from_zip(zip_path, destination=dest)

        assert dest.is_dir()
        assert 'proj' in result

    def test_ignores_other_project_cif_in_destination(self, tmp_path):
        """Only finds project.edstar from the zip, not pre-existing ones."""
        dest = tmp_path / 'data'
        # Pre-create another project directory in the destination
        other_project = dest / 'aaa_other' / 'project.edstar'
        other_project.parent.mkdir(parents=True)
        other_project.write_text('other\n')

        zip_path = tmp_path / 'proj.zip'
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('target_project/project.edstar', 'correct\n')

        result = extract_project_from_zip(zip_path, destination=dest)

        assert 'target_project' in result
        assert 'aaa_other' not in result


class TestExtractDataPathsFromZip:
    """Tests for extract_data_paths_from_zip."""

    def test_extracts_to_temp_dir_by_default(self, tmp_path):
        """Without destination, files go to a temp directory."""
        zip_path = tmp_path / 'test.zip'
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('scan_001.dat', '1 2 3\n')
            zf.writestr('scan_002.dat', '4 5 6\n')

        paths = extract_data_paths_from_zip(zip_path)

        assert len(paths) == 2
        assert 'scan_001.dat' in paths[0]
        assert 'scan_002.dat' in paths[1]

    def test_extracts_to_destination(self, tmp_path):
        """With destination, files go to the specified directory."""
        zip_path = tmp_path / 'test.zip'
        dest = tmp_path / 'output'
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('scan_001.dat', '1 2 3\n')
            zf.writestr('scan_002.dat', '4 5 6\n')

        paths = extract_data_paths_from_zip(zip_path, destination=dest)

        assert len(paths) == 2
        assert all(str(dest) in p for p in paths)
        assert (dest / 'scan_001.dat').is_file()
        assert (dest / 'scan_002.dat').is_file()

    def test_destination_creates_directory(self, tmp_path):
        """Destination directory is created if it does not exist."""
        zip_path = tmp_path / 'test.zip'
        dest = tmp_path / 'nested' / 'output'
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('data.dat', '1 2 3\n')

        paths = extract_data_paths_from_zip(zip_path, destination=dest)

        assert len(paths) == 1
        assert dest.is_dir()

    def test_relative_destination_does_not_depend_on_current_project(self, tmp_path, monkeypatch):
        """Relative destinations are resolved from cwd, not project state."""
        zip_path = tmp_path / 'test.zip'
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('scan_001.dat', '1 2 3\n')

        workspace = tmp_path / 'workspace'
        workspace.mkdir()
        monkeypatch.chdir(workspace)
        # With no artifact root configured, relative destinations resolve
        # against the cwd. Clear the env var so the test does not depend on
        # whether a sibling test happened to leave it set.
        monkeypatch.delenv('EASYDIFFRACTION_ARTIFACT_ROOT', raising=False)

        original_current_project = Project._current_project
        try:
            Project._loading = True
            project_one = Project()
            project_two = Project()
        finally:
            Project._loading = False

        try:
            project_one.save_as(str(tmp_path / 'project-one'))
            project_two.save_as(str(tmp_path / 'project-two'))
            paths = extract_data_paths_from_zip(zip_path, destination='data/d20_scan')
        finally:
            Project._current_project = original_current_project

        assert len(paths) == 1
        assert Path(paths[0]).parent == (workspace / 'data' / 'd20_scan').resolve()

    def test_raises_file_not_found(self, tmp_path):
        """Raises FileNotFoundError for missing ZIP path."""
        with pytest.raises(FileNotFoundError):
            extract_data_paths_from_zip(tmp_path / 'missing.zip')

    def test_raises_value_error_for_empty_zip(self, tmp_path):
        """Raises ValueError when ZIP has no usable files."""
        zip_path = tmp_path / 'empty.zip'
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('.hidden', 'hidden\n')

        with pytest.raises(ValueError, match='No data files found'):
            extract_data_paths_from_zip(zip_path)

    def test_excludes_hidden_files(self, tmp_path):
        """Hidden files are excluded from returned paths."""
        zip_path = tmp_path / 'test.zip'
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('data.dat', '1 2 3\n')
            zf.writestr('.hidden', 'hidden\n')
            zf.writestr('__meta', 'meta\n')

        paths = extract_data_paths_from_zip(zip_path)

        assert len(paths) == 1
        assert 'data.dat' in paths[0]

    def test_returns_sorted_paths(self, tmp_path):
        """Returned paths are sorted lexicographically."""
        zip_path = tmp_path / 'test.zip'
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('c.dat', '3\n')
            zf.writestr('a.dat', '1\n')
            zf.writestr('b.dat', '2\n')

        paths = extract_data_paths_from_zip(zip_path)

        assert 'a.dat' in paths[0]
        assert 'b.dat' in paths[1]
        assert 'c.dat' in paths[2]


class TestExtractDataPathsFromDir:
    """Tests for extract_data_paths_from_dir."""

    def test_lists_files_in_directory(self, tmp_path):
        """Returns sorted paths for files in a directory."""
        (tmp_path / 'scan_002.dat').write_text('2\n')
        (tmp_path / 'scan_001.dat').write_text('1\n')

        paths = extract_data_paths_from_dir(tmp_path)

        assert len(paths) == 2
        assert 'scan_001.dat' in paths[0]
        assert 'scan_002.dat' in paths[1]

    def test_lists_absolute_paths_for_relative_directory(self, tmp_path, monkeypatch):
        """Returns absolute paths even when the input directory is relative."""
        data_dir = tmp_path / 'scans'
        data_dir.mkdir()
        (data_dir / 'scan_002.dat').write_text('2\n')
        (data_dir / 'scan_001.dat').write_text('1\n')
        monkeypatch.chdir(tmp_path)

        paths = extract_data_paths_from_dir('scans')

        assert paths == [
            str((data_dir / 'scan_001.dat').resolve()),
            str((data_dir / 'scan_002.dat').resolve()),
        ]

    def test_raises_for_missing_directory(self, tmp_path):
        """Raises FileNotFoundError for non-existent directory."""
        with pytest.raises(FileNotFoundError):
            extract_data_paths_from_dir(tmp_path / 'missing')

    def test_raises_for_empty_directory(self, tmp_path):
        """Raises ValueError when directory has no matching files."""
        empty = tmp_path / 'empty'
        empty.mkdir()

        with pytest.raises(ValueError, match='No files matching'):
            extract_data_paths_from_dir(empty)
