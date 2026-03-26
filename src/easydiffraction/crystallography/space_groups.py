# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""
Space group reference data.

Loads a gzipped, packaged pickle with crystallographic space-group
information. The file is part of the distribution; user input is not
involved.
"""

import gzip
import pickle  # noqa: S403 - trusted internal pickle file (package data only)
from pathlib import Path


def _restricted_pickle_load(file_obj: object) -> object:
    """
    Load pickle data from an internal gz file (trusted boundary).

    The archive lives in the package; no user-controlled input enters
    this function. If distribution process changes, revisit.
    """
    data = pickle.load(file_obj)  # noqa: S301 - trusted internal pickle (see docstring)
    return data


def _load() -> object:
    """Load space-group data from the packaged archive."""
    path = Path(__file__).with_name('space_groups.pkl.gz')
    with gzip.open(path, 'rb') as f:
        return _restricted_pickle_load(f)


SPACE_GROUPS = _load()
