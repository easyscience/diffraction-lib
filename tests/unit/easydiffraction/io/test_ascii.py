# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for extract_project_from_zip, extract_data_paths_from_zip and extract_data_paths_from_dir."""

from __future__ import annotations

import zipfile

import pytest

from easydiffraction.io.ascii import extract_data_paths_from_dir
from easydiffraction.io.ascii import extract_data_paths_from_zip
from easydiffraction.io.ascii import extract_project_from_zip


class TestExtractProjectFromZip:
    """Tests for extract_project_from_zip."""

    def test_extracts_project_dir(self, tmp_path):
        """Returns path to the directory containing project.cif."""
        zip_path = tmp_path / 'proj.zip'
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('my_project/project.cif', 'data_project\n')
            zf.writestr('my_project/structures/struct.cif', 'data_struct\n')

        result = extract_project_from_zip(zip_path, destination=tmp_path / 'out')

        assert result.endswith('my_project')
        assert (tmp_path / 'out' / 'my_project' / 'project.cif').is_file()

    def test_extracts_to_temp_dir_by_default(self, tmp_path):
        """Without destination, files go to a temp directory."""
        zip_path = tmp_path / 'proj.zip'
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('myproj/project.cif', 'data_project\n')

        result = extract_project_from_zip(zip_path)

        assert 'myproj' in result
        assert 'project.cif' not in result  # returns parent dir, not file

    def test_raises_file_not_found(self, tmp_path):
        """Raises FileNotFoundError for missing ZIP path."""
        with pytest.raises(FileNotFoundError):
            extract_project_from_zip(tmp_path / 'missing.zip')

    def test_raises_value_error_no_project_cif(self, tmp_path):
        """Raises ValueError when ZIP has no project.cif."""
        zip_path = tmp_path / 'bad.zip'
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('data.dat', '1 2 3\n')

        with pytest.raises(ValueError, match=r'No project\.cif found'):
            extract_project_from_zip(zip_path)

    def test_destination_creates_directory(self, tmp_path):
        """Destination directory is created if it does not exist."""
        zip_path = tmp_path / 'proj.zip'
        dest = tmp_path / 'nested' / 'output'
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('proj/project.cif', 'data\n')

        result = extract_project_from_zip(zip_path, destination=dest)

        assert dest.is_dir()
        assert 'proj' in result

    def test_ignores_other_project_cif_in_destination(self, tmp_path):
        """Only finds project.cif from the zip, not pre-existing ones."""
        dest = tmp_path / 'data'
        # Pre-create another project directory in the destination
        other_project = dest / 'aaa_other' / 'project.cif'
        other_project.parent.mkdir(parents=True)
        other_project.write_text('other\n')

        zip_path = tmp_path / 'proj.zip'
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('target_project/project.cif', 'correct\n')

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
