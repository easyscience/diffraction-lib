# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Helpers for loading numeric data from ASCII files."""

from __future__ import annotations

import tempfile
import zipfile
from io import StringIO
from pathlib import Path

import numpy as np


def extract_data_paths_from_zip(zip_path: str | Path) -> list[str]:
    """
    Extract all files from a ZIP archive and return their paths.

    Files are extracted into a temporary directory that persists for the
    lifetime of the process.  The returned paths are sorted
    lexicographically by file name so that numbered data files (e.g.
    ``scan_001.dat``, ``scan_002.dat``) appear in natural order. Hidden
    files and directories (names starting with ``'.'`` or ``'__'``) are
    excluded.

    Parameters
    ----------
    zip_path : str | Path
        Path to the ZIP archive.

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
        raise FileNotFoundError(f'ZIP file not found: {zip_path}')

    extract_dir = Path(tempfile.mkdtemp(prefix='ed_zip_'))

    with zipfile.ZipFile(zip_path, 'r') as zf:
        zf.extractall(extract_dir)

    paths = sorted(
        str(p)
        for p in extract_dir.rglob('*')
        if p.is_file() and not p.name.startswith('.') and not p.name.startswith('__')
    )

    if not paths:
        raise ValueError(f'No data files found in ZIP archive: {zip_path}')

    return paths


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
    IOError
        If no contiguous numeric block can be found in the file.
    """
    data_path = Path(data_path)
    lines = data_path.read_text().splitlines()

    last_error: Exception | None = None
    for start in range(len(lines)):
        try:
            return np.loadtxt(StringIO('\n'.join(lines[start:])))
        except Exception as e:  # noqa: BLE001
            last_error = e

    raise IOError(
        f'Failed to read numeric data from {data_path}: {last_error}',
    ) from last_error
