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
        zf.extractall(extract_dir)

    # Find the project directory (the one containing project.cif)
    project_cifs = list(extract_dir.rglob('project.cif'))
    if not project_cifs:
        msg = f'No project.cif found in ZIP archive: {zip_path}'
        raise ValueError(msg)

    return str(project_cifs[0].parent.resolve())


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
        directory is created.

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

    if destination is not None:
        extract_dir = Path(destination)
        extract_dir.mkdir(parents=True, exist_ok=True)
    else:
        # TODO: Unify mkdir with other uses in the code
        extract_dir = Path(tempfile.mkdtemp(prefix='ed_zip_'))

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
    Load a numeric block from an ASCII file, skipping header lines.

    Read the file and try ``numpy.loadtxt`` starting from the first
    line, then the second, etc., until the load succeeds.  This allows
    files with an arbitrary number of non-numeric header lines to be
    parsed without prior knowledge of the format.

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
        If no contiguous numeric block can be found in the file.
    """
    data_path = Path(data_path)
    lines = data_path.read_text().splitlines()

    last_error: Exception | None = None
    for start in range(len(lines)):
        try:
            return np.loadtxt(StringIO('\n'.join(lines[start:])))
        except Exception as e:
            last_error = e

    msg = f'Failed to read numeric data from {data_path}: {last_error}'
    raise OSError(
        msg,
    ) from last_error
