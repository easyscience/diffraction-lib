# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for utils/environment.py."""


class TestInPytest:
    def test_returns_true_in_pytest(self):
        from easydiffraction.utils.environment import in_pytest

        assert in_pytest() is True


class TestInWarp:
    def test_false_by_default(self):
        from easydiffraction.utils.environment import in_warp

        # Unless running in Warp terminal
        import os

        if os.getenv('TERM_PROGRAM') != 'WarpTerminal':
            assert in_warp() is False

    def test_true_with_env_var(self, monkeypatch):
        from easydiffraction.utils.environment import in_warp

        monkeypatch.setenv('TERM_PROGRAM', 'WarpTerminal')
        assert in_warp() is True


class TestInPycharm:
    def test_false_by_default(self, monkeypatch):
        from easydiffraction.utils.environment import in_pycharm

        monkeypatch.delenv('PYCHARM_HOSTED', raising=False)
        assert in_pycharm() is False

    def test_true_with_env_var(self, monkeypatch):
        from easydiffraction.utils.environment import in_pycharm

        monkeypatch.setenv('PYCHARM_HOSTED', '1')
        assert in_pycharm() is True


class TestInJupyter:
    def test_false_in_tests(self):
        from easydiffraction.utils.environment import in_jupyter

        assert in_jupyter() is False


class TestInGithubCi:
    def test_false_without_env(self, monkeypatch):
        from easydiffraction.utils.environment import in_github_ci

        monkeypatch.delenv('GITHUB_ACTIONS', raising=False)
        assert in_github_ci() is False

    def test_true_with_env(self, monkeypatch):
        from easydiffraction.utils.environment import in_github_ci

        monkeypatch.setenv('GITHUB_ACTIONS', 'true')
        assert in_github_ci() is True


class TestIpythonHelpers:
    def test_is_ipython_display_handle_with_none(self):
        from easydiffraction.utils.environment import is_ipython_display_handle

        assert is_ipython_display_handle(None) is False

    def test_is_ipython_display_handle_with_string(self):
        from easydiffraction.utils.environment import is_ipython_display_handle

        assert is_ipython_display_handle('not a handle') is False

    def test_can_update_ipython_display(self):
        from easydiffraction.utils.environment import can_update_ipython_display

        # IPython is installed in our test environment
        result = can_update_ipython_display()
        assert isinstance(result, bool)

    def test_can_use_ipython_display_with_none(self):
        from easydiffraction.utils.environment import can_use_ipython_display

        assert can_use_ipython_display(None) is False
