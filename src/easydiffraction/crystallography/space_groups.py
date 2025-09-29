# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

import gzip
import pickle  # noqa: S403 - trusted internal pickle file (package data only)
from pathlib import Path
from typing import Any


def _restricted_pickle_load(file_obj) -> Any:
    """Load pickle data from an internal gz file (trusted boundary).

    The archive lives in the package; no user-controlled input enters
    this function. If distribution process changes, revisit.
    """
    data = pickle.load(file_obj)  # noqa: S301 - trusted internal pickle (see docstring)
    return data


def _load():
    path = Path(__file__).with_name('space_groups.pkl.gz')
    with gzip.open(path, 'rb') as f:
        return _restricted_pickle_load(f)


SPACE_GROUPS = _load()
