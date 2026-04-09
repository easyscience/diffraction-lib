# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Additional unit tests for space_groups.py to cover RestrictedUnpickler."""

import io
import pickle  # noqa: S403

import pytest


class TestRestrictedUnpickler:
    def test_loads_plain_dict(self):
        """Safe built-in types should be allowed."""
        from easydiffraction.crystallography.space_groups import _restricted_pickle_load

        data = {'key': [1, 2, 3], 'nested': {'a': (True, None)}}
        buf = io.BytesIO()
        pickle.dump(data, buf)
        buf.seek(0)
        result = _restricted_pickle_load(buf)
        assert result == data

    def test_loads_set_and_frozenset(self):
        from easydiffraction.crystallography.space_groups import _restricted_pickle_load

        data = {'s': {1, 2}, 'fs': frozenset({3, 4})}
        buf = io.BytesIO()
        pickle.dump(data, buf)
        buf.seek(0)
        result = _restricted_pickle_load(buf)
        assert result == data

    def test_loads_tuple_and_list(self):
        from easydiffraction.crystallography.space_groups import _restricted_pickle_load

        data = ([1, 2], (3, 4))
        buf = io.BytesIO()
        pickle.dump(data, buf)
        buf.seek(0)
        result = _restricted_pickle_load(buf)
        assert result == data

    def test_rejects_unsafe_class(self):
        """Non-builtin types should be rejected."""
        from easydiffraction.crystallography.space_groups import _RestrictedUnpickler

        # Create a pickle stream that tries to instantiate os.system
        buf = io.BytesIO()
        # Use protocol 2 to get GLOBAL opcode
        pickle.dump(object(), buf, protocol=2)
        buf.seek(0)

        # Directly test find_class rejection
        unpickler = _RestrictedUnpickler(buf)
        with pytest.raises(pickle.UnpicklingError, match='Restricted unpickler refused'):
            unpickler.find_class('os', 'system')

    def test_rejects_builtins_not_in_safe_set(self):
        from easydiffraction.crystallography.space_groups import _RestrictedUnpickler

        buf = io.BytesIO(b'')
        unpickler = _RestrictedUnpickler(buf)
        with pytest.raises(pickle.UnpicklingError, match='Restricted unpickler refused'):
            unpickler.find_class('builtins', 'eval')

    def test_space_groups_loaded_successfully(self):
        """The SPACE_GROUPS constant should be a non-empty dict."""
        from easydiffraction.crystallography.space_groups import SPACE_GROUPS

        assert isinstance(SPACE_GROUPS, dict)
        assert len(SPACE_GROUPS) > 0
