# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Additional unit tests for environment.py to cover BLE001 branches."""


class TestCanUpdateIpythonDisplay:
    def test_returns_bool(self):
        from easydiffraction.utils.environment import can_update_ipython_display

        result = can_update_ipython_display()
        assert isinstance(result, bool)


class TestIsIpythonDisplayHandleEdgeCases:
    def test_with_int(self):
        from easydiffraction.utils.environment import is_ipython_display_handle

        assert is_ipython_display_handle(42) is False

    def test_with_dict(self):
        from easydiffraction.utils.environment import is_ipython_display_handle

        assert is_ipython_display_handle({}) is False

    def test_with_class_missing_module(self):
        """Object whose __class__ has no __module__ attribute."""
        from easydiffraction.utils.environment import is_ipython_display_handle

        class NoModule:
            pass

        assert is_ipython_display_handle(NoModule()) is False


class TestCanUseIpythonDisplay:
    def test_with_plain_string(self):
        from easydiffraction.utils.environment import can_use_ipython_display

        assert can_use_ipython_display('hello') is False

    def test_with_int(self):
        from easydiffraction.utils.environment import can_use_ipython_display

        assert can_use_ipython_display(123) is False


class TestInColab:
    def test_returns_false_outside_colab(self):
        from easydiffraction.utils.environment import in_colab

        # Unless running in Colab
        assert in_colab() is False
