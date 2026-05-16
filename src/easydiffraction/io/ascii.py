# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Helpers for loading numeric data from ASCII files."""

from __future__ import annotations

import re
import tempfile
import zipfile
from io import StringIO
from pathlib import Path

import numpy as np


def _resolve_extraction_destination(destination: str | Path | None) -> Path:
    """Return an extraction directory for ZIP contents."""
    if destination is None:
        return Path(tempfile.mkdtemp(prefix='ed_zip_'))

    extract_dir = Path(destination)
    if not extract_dir.is_absolute():
        from easydiffraction.project.project import Project  # noqa: PLC0415

        project_path = Project.current_project_path()
        if project_path is not None:
            extract_dir = project_path / extract_dir

    extract_dir.mkdir(parents=True, exist_ok=True)
    return extract_dir


def extract_project_from_zip(
    zip_path: str | Path,
    destination: str | Path | None = None,
) -> str:
    """
    Extract a project directory from a ZIP archive.

    The archive must contain exactly one directory with a
    ``project.cif`` file.  Files are extracted into *destination* when
    provided, or into a temporary directory that persists for the
    lifetime of the process.

    Parameters
    ----------
    zip_path : str | Path
        Path to the ZIP archive containing the project.
    destination : str | Path | None, default=None
        Directory to extract into.  When ``None``, a temporary directory
        is created.

    Returns
    -------
    str
        Absolute path to the extracted project directory (the directory
        that contains ``project.cif``).

    Raises
    ------
    FileNotFoundError
        If *zip_path* does not exist.
    ValueError
        If the archive does not contain a ``project.cif`` file.
    """
    zip_path = Path(zip_path)
    if not zip_path.exists():
        msg = f'ZIP file not found: {zip_path}'
        raise FileNotFoundError(msg)

    if destination is not None:
        extract_dir = Path(destination)
        extract_dir.mkdir(parents=True, exist_ok=True)
    else:
        extract_dir = Path(tempfile.mkdtemp(prefix='ed_zip_'))

    with zipfile.ZipFile(zip_path, 'r') as zf:
        # Determine the project directory from the archive contents
        # *before* extraction, so we are not confused by unrelated
        # project.cif files already present in the destination.
        project_cif_entries = [name for name in zf.namelist() if name.endswith('project.cif')]
        if not project_cif_entries:
            msg = f'No project.cif found in ZIP archive: {zip_path}'
            raise ValueError(msg)

        zf.extractall(extract_dir)

    project_cif_path = extract_dir / project_cif_entries[0]
    return str(project_cif_path.parent.resolve())


def extract_data_paths_from_zip(
    zip_path: str | Path,
    destination: str | Path | None = None,
) -> list[str]:
    """
    Extract all files from a ZIP archive and return their paths.

    Files are extracted into *destination* when provided, or into a
    temporary directory that persists for the lifetime of the process.
    The returned paths are sorted lexicographically by file name so that
    numbered data files (e.g. ``scan_001.dat``, ``scan_002.dat``) appear
    in natural order. Hidden files and directories (names starting with
    ``'.'`` or ``'__'``) are excluded.

    Parameters
    ----------
    zip_path : str | Path
        Path to the ZIP archive.
    destination : str | Path | None, default=None
        Directory to extract files into.  When ``None``, a temporary
        directory is created. Relative destinations are resolved against
        the current saved project path when one exists.

    Returns
    -------
    list[str]
        Sorted absolute paths to the extracted data files.

    Raises
    ------
    FileNotFoundError
        If *zip_path* does not exist.
    ValueError
        If the archive contains no usable data files.
    """
    zip_path = Path(zip_path)
    if not zip_path.exists():
        msg = f'ZIP file not found: {zip_path}'
        raise FileNotFoundError(msg)

    extract_dir = _resolve_extraction_destination(destination)

    with zipfile.ZipFile(zip_path, 'r') as zf:
        zf.extractall(extract_dir)

    paths = sorted(
        str(p)
        for p in extract_dir.rglob('*')
        if p.is_file() and not p.name.startswith('.') and not p.name.startswith('__')
    )

    if not paths:
        msg = f'No data files found in ZIP archive: {zip_path}'
        raise ValueError(msg)

    return paths


def extract_data_paths_from_dir(
    dir_path: str | Path,
    file_pattern: str = '*',
) -> list[str]:
    """
    List data files in a directory and return their sorted paths.

    Hidden files (names starting with ``'.'`` or ``'__'``) are excluded.
    The returned paths are sorted lexicographically by file name.

    Parameters
    ----------
    dir_path : str | Path
        Path to the directory containing data files.
    file_pattern : str, default='*'
        Glob pattern to filter files (e.g. ``'*.dat'``, ``'*.xye'``).

    Returns
    -------
    list[str]
        Sorted absolute paths to the matching data files.

    Raises
    ------
    FileNotFoundError
        If *dir_path* does not exist or is not a directory.
    ValueError
        If no matching data files are found.
    """
    dir_path = Path(dir_path)
    if not dir_path.is_dir():
        msg = f'Directory not found: {dir_path}'
        raise FileNotFoundError(msg)

    paths = sorted(
        str(p)
        for p in dir_path.glob(file_pattern)
        if p.is_file() and not p.name.startswith('.') and not p.name.startswith('__')
    )

    if not paths:
        msg = f"No files matching '{file_pattern}' found in directory: {dir_path}"
        raise ValueError(msg)

    return paths


def extract_metadata(
    file_path: str | Path,
    pattern: str,
) -> float | None:
    """
    Extract a single numeric value from a file using a regex pattern.

    The entire file content is searched (not just the header).  The
    **first** match is used.  The regex must contain exactly one capture
    group whose match is convertible to ``float``.

    Parameters
    ----------
    file_path : str | Path
        Path to the input file.
    pattern : str
        Regex with one capture group that matches the numeric value.

    Returns
    -------
    float | None
        The extracted value, or ``None`` if the pattern did not match or
        the captured text could not be converted to float.
    """
    content = Path(file_path).read_text(encoding='utf-8', errors='ignore')
    match = re.search(pattern, content, re.MULTILINE)
    if match is None:
        return None
    try:
        return float(match.group(1))
    except (ValueError, IndexError):
        return None


def load_numeric_block(data_path: str | Path) -> np.ndarray:
    """
    Load a numeric block from an ASCII file, skipping non-numeric lines.

    Each line is tested individually: lines whose whitespace-separated
    tokens are all valid floats are kept; everything else (headers,
    footers, comment lines) is silently discarded.

    Parameters
    ----------
    data_path : str | Path
        Path to the ASCII data file.

    Returns
    -------
    np.ndarray
        2-D array of the parsed numeric data.

    Raises
    ------
    OSError
        If no numeric lines can be found in the file.
    """
    data_path = Path(data_path)
    lines = data_path.read_text().splitlines()

    numeric_lines: list[str] = []
    for line in lines:
        tokens = line.split()
        if not tokens:
            continue
        try:
            for token in tokens:
                float(token)
        except ValueError:
            continue
        numeric_lines.append(line)

    if not numeric_lines:
        msg = f'Failed to read numeric data from {data_path}: no numeric lines found'
        raise OSError(msg)

    return np.loadtxt(StringIO('\n'.join(numeric_lines)))
