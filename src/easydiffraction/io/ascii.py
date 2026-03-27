# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Helpers for loading numeric data from ASCII files."""

from __future__ import annotations

from io import StringIO
from pathlib import Path

import numpy as np


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
