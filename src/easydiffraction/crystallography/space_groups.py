# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""
Space group reference data.

Loads a gzipped, packaged pickle with crystallographic space-group
information. The file is part of the distribution; user input is not
involved.
"""

import builtins
import gzip
import io
import pickle  # noqa: S403
from pathlib import Path
from typing import override

_SAFE_BUILTINS = frozenset({
    'dict',
    'frozenset',
    'list',
    'set',
    'tuple',
})


class _RestrictedUnpickler(pickle.Unpickler):  # noqa: S301
    """
    Unpickler that only allows safe built-in types.

    Rejects any ``GLOBAL`` opcode that references modules or classes
    outside of ``builtins``, limiting deserialisation to plain Python
    data structures (dicts, lists, tuples, sets, frozensets) plus
    primitive scalars (str, int, float, bool, None) which the pickle
    protocol handles without ``GLOBAL``.
    """

    @override
    def find_class(
        self,
        module: str,
        name: str,
    ) -> type:
        """
        Allow only safe built-in types.

        Parameters
        ----------
        module : str
            The module name from the pickle stream.
        name : str
            The class/function name from the pickle stream.

        Returns
        -------
        type
            The resolved built-in type.

        Raises
        ------
        pickle.UnpicklingError
            If the requested type is not in the safe set.
        """
        if module == 'builtins' and name in _SAFE_BUILTINS:
            return getattr(builtins, name)
        msg = f'Restricted unpickler refused {module}.{name}'
        raise pickle.UnpicklingError(msg)


def _restricted_pickle_load(file_obj: io.BufferedIOBase) -> object:
    """
    Load pickle data using a restricted unpickler.

    Only safe built-in types (dict, list, tuple, set, frozenset, and
    primitive scalars) are permitted. The archive lives in the package;
    no user-controlled input enters this function.

    Parameters
    ----------
    file_obj : io.BufferedIOBase
        Binary file object to read pickle data from.

    Returns
    -------
    object
        The deserialised Python data structure.
    """
    return _RestrictedUnpickler(file_obj).load()


def _load() -> object:
    """Load space-group data from the packaged archive."""
    path = Path(__file__).with_name('space_groups.pkl.gz')
    with gzip.open(path, 'rb') as f:
        return _restricted_pickle_load(f)


SPACE_GROUPS = _load()
