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


class TestArtifactPaths:
    def test_resolve_artifact_path_uses_env_root(self, monkeypatch, tmp_path):
        from easydiffraction.utils.environment import resolve_artifact_path

        monkeypatch.setenv('EASYDIFFRACTION_ARTIFACT_ROOT', 'tmp/tutorials')
        monkeypatch.setenv('PIXI_PROJECT_ROOT', str(tmp_path))

        assert resolve_artifact_path('data') == tmp_path / 'tmp' / 'tutorials' / 'data'

    def test_resolve_artifact_path_uses_tutorial_fallback(self, monkeypatch, tmp_path):
        import easydiffraction.utils.environment as env

        repo_root = tmp_path / 'repo'
        tutorials_dir = repo_root / 'docs' / 'docs' / 'tutorials'
        tutorials_dir.mkdir(parents=True)

        monkeypatch.delenv('EASYDIFFRACTION_ARTIFACT_ROOT', raising=False)
        monkeypatch.delenv('PIXI_PROJECT_ROOT', raising=False)
        monkeypatch.chdir(tutorials_dir)
        monkeypatch.setattr(env, '_repo_root', lambda: repo_root)

        assert env.resolve_artifact_path('data') == repo_root / 'tmp' / 'tutorials' / 'data'

    def test_create_artifact_temp_dir_uses_tutorial_fallback(self, monkeypatch, tmp_path):
        import easydiffraction.utils.environment as env

        repo_root = tmp_path / 'repo'
        tutorials_dir = repo_root / 'docs' / 'docs' / 'tutorials'
        tutorials_dir.mkdir(parents=True)

        monkeypatch.delenv('EASYDIFFRACTION_ARTIFACT_ROOT', raising=False)
        monkeypatch.delenv('PIXI_PROJECT_ROOT', raising=False)
        monkeypatch.chdir(tutorials_dir)
        monkeypatch.setattr(env, '_repo_root', lambda: repo_root)

        created_dir = env.create_artifact_temp_dir('ed_zip_')

        assert created_dir.is_dir()
        assert created_dir.parent == repo_root / 'tmp' / 'tutorials'


class TestResolveFigureEmbedMode:
    def test_unset_defaults_to_inline(self, monkeypatch):
        from easydiffraction.utils.environment import FigureEmbedMode
        from easydiffraction.utils.environment import resolve_figure_embed_mode

        monkeypatch.delenv('EASYDIFFRACTION_FIGURE_EMBED_MODE', raising=False)
        assert resolve_figure_embed_mode() is FigureEmbedMode.INLINE

    def test_blank_defaults_to_inline(self, monkeypatch):
        from easydiffraction.utils.environment import FigureEmbedMode
        from easydiffraction.utils.environment import resolve_figure_embed_mode

        monkeypatch.setenv('EASYDIFFRACTION_FIGURE_EMBED_MODE', '   ')
        assert resolve_figure_embed_mode() is FigureEmbedMode.INLINE

    def test_shared_and_standalone_case_insensitive(self, monkeypatch):
        from easydiffraction.utils.environment import FigureEmbedMode
        from easydiffraction.utils.environment import resolve_figure_embed_mode

        monkeypatch.setenv('EASYDIFFRACTION_FIGURE_EMBED_MODE', 'shared')
        assert resolve_figure_embed_mode() is FigureEmbedMode.SHARED
        monkeypatch.setenv('EASYDIFFRACTION_FIGURE_EMBED_MODE', 'STANDALONE')
        assert resolve_figure_embed_mode() is FigureEmbedMode.STANDALONE

    def test_unknown_value_raises_with_details(self, monkeypatch):
        import pytest

        from easydiffraction.utils.environment import resolve_figure_embed_mode

        monkeypatch.setenv('EASYDIFFRACTION_FIGURE_EMBED_MODE', 'bogus')
        with pytest.raises(ValueError, match='bogus') as exc_info:
            resolve_figure_embed_mode()
        message = str(exc_info.value)
        assert 'bogus' in message
        for mode in ('inline', 'shared', 'standalone'):
            assert mode in message
