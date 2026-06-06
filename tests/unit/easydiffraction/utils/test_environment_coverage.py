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


class TestRepoRoot:
    def test_uses_pixi_project_root_env_var(self, monkeypatch, tmp_path):
        import easydiffraction.utils.environment as env

        monkeypatch.setenv('PIXI_PROJECT_ROOT', str(tmp_path))

        assert env._repo_root() == tmp_path.resolve()

    def test_walks_filesystem_when_env_var_unset(self, monkeypatch):
        import easydiffraction.utils.environment as env

        monkeypatch.delenv('PIXI_PROJECT_ROOT', raising=False)

        repo_root = env._repo_root()

        # The real repository ships pixi.toml and the tutorials dir, so the
        # parent walk must resolve to a directory containing both markers.
        assert repo_root is not None
        assert (repo_root / 'pixi.toml').is_file()
        assert (repo_root / env._TUTORIALS_DIR).is_dir()

    def test_returns_none_when_no_marker_found(self, monkeypatch):
        from pathlib import Path

        import easydiffraction.utils.environment as env

        monkeypatch.delenv('PIXI_PROJECT_ROOT', raising=False)
        # Point the tutorials marker at a directory no ancestor contains so
        # the parent walk exhausts without a match.
        monkeypatch.setattr(env, '_TUTORIALS_DIR', Path('this_marker_never_exists_xyz'))

        assert env._repo_root() is None


class TestTutorialArtifactRoot:
    def test_returns_none_when_repo_root_missing(self, monkeypatch):
        import easydiffraction.utils.environment as env

        monkeypatch.setattr(env, '_repo_root', lambda: None)

        assert env._tutorial_artifact_root() is None

    def test_returns_none_when_cwd_outside_tutorials(self, monkeypatch, tmp_path):
        import easydiffraction.utils.environment as env

        repo_root = tmp_path / 'repo'
        (repo_root / 'docs' / 'docs' / 'tutorials').mkdir(parents=True)
        outside = tmp_path / 'elsewhere'
        outside.mkdir()

        monkeypatch.setattr(env, '_repo_root', lambda: repo_root)
        monkeypatch.chdir(outside)

        assert env._tutorial_artifact_root() is None


class TestArtifactRootResolution:
    def test_relative_root_without_pixi_uses_cwd(self, monkeypatch, tmp_path):
        from easydiffraction.utils.environment import resolve_artifact_path

        monkeypatch.setenv('EASYDIFFRACTION_ARTIFACT_ROOT', 'artifacts')
        monkeypatch.delenv('PIXI_PROJECT_ROOT', raising=False)
        monkeypatch.chdir(tmp_path)

        resolved = resolve_artifact_path('data')

        assert resolved == (tmp_path / 'artifacts' / 'data').resolve()

    def test_absolute_root_used_as_is(self, monkeypatch, tmp_path):
        from easydiffraction.utils.environment import resolve_artifact_path

        monkeypatch.setenv('EASYDIFFRACTION_ARTIFACT_ROOT', str(tmp_path))
        monkeypatch.delenv('PIXI_PROJECT_ROOT', raising=False)

        assert resolve_artifact_path('data') == (tmp_path / 'data').resolve()


class TestCreateArtifactTempDirNoRoot:
    def test_uses_system_tempdir_when_no_artifact_root(self, monkeypatch):
        import easydiffraction.utils.environment as env

        monkeypatch.setattr(env, '_artifact_root', lambda: None)

        created_dir = env.create_artifact_temp_dir('ed_no_root_')

        try:
            assert created_dir.is_dir()
            assert created_dir.name.startswith('ed_no_root_')
        finally:
            created_dir.rmdir()


class TestInJupyterBranches:
    def test_false_when_in_pycharm(self, monkeypatch):
        import easydiffraction.utils.environment as env

        monkeypatch.setattr(env, 'in_pycharm', lambda: True)

        assert env.in_jupyter() is False

    def test_true_when_in_colab(self, monkeypatch):
        import easydiffraction.utils.environment as env

        monkeypatch.setattr(env, 'in_pycharm', lambda: False)
        monkeypatch.setattr(env, 'in_colab', lambda: True)

        assert env.in_jupyter() is True

    def test_true_for_ipkernel_config(self, monkeypatch):
        import IPython

        import easydiffraction.utils.environment as env

        monkeypatch.setattr(env, 'in_pycharm', lambda: False)
        monkeypatch.setattr(env, 'in_colab', lambda: False)

        class FakeShell:
            config = {'IPKernelApp': {}}

        shell = FakeShell()
        monkeypatch.setattr(IPython, 'get_ipython', lambda: shell)

        assert env.in_jupyter() is True

    def test_true_for_zmq_interactive_shell(self, monkeypatch):
        import IPython

        import easydiffraction.utils.environment as env

        monkeypatch.setattr(env, 'in_pycharm', lambda: False)
        monkeypatch.setattr(env, 'in_colab', lambda: False)

        class ZMQInteractiveShell:
            config = {}

        shell = ZMQInteractiveShell()
        monkeypatch.setattr(IPython, 'get_ipython', lambda: shell)

        assert env.in_jupyter() is True

    def test_false_when_get_ipython_returns_none(self, monkeypatch):
        import IPython

        import easydiffraction.utils.environment as env

        monkeypatch.setattr(env, 'in_pycharm', lambda: False)
        monkeypatch.setattr(env, 'in_colab', lambda: False)
        monkeypatch.setattr(IPython, 'get_ipython', lambda: None)

        assert env.in_jupyter() is False

    def test_false_for_plain_terminal_shell(self, monkeypatch):
        import IPython

        import easydiffraction.utils.environment as env

        monkeypatch.setattr(env, 'in_pycharm', lambda: False)
        monkeypatch.setattr(env, 'in_colab', lambda: False)

        class TerminalInteractiveShell:
            config = {}

        shell = TerminalInteractiveShell()
        monkeypatch.setattr(IPython, 'get_ipython', lambda: shell)

        assert env.in_jupyter() is False


class TestIsIpythonDisplayHandleFallback:
    def _force_import_error(self, monkeypatch):
        """Make ``from IPython.display import DisplayHandle`` fail."""
        import sys
        import types

        # A bare module object without ``DisplayHandle`` triggers ImportError
        # on the ``from ... import DisplayHandle`` statement.
        monkeypatch.setitem(sys.modules, 'IPython.display', types.ModuleType('IPython.display'))

    def test_fallback_true_for_ipython_module_class(self, monkeypatch):
        from easydiffraction.utils.environment import is_ipython_display_handle

        self._force_import_error(monkeypatch)

        class FakeHandle:
            pass

        FakeHandle.__module__ = 'IPython.display'

        assert is_ipython_display_handle(FakeHandle()) is True

    def test_fallback_false_for_non_ipython_class(self, monkeypatch):
        from easydiffraction.utils.environment import is_ipython_display_handle

        self._force_import_error(monkeypatch)

        class PlainHandle:
            pass

        PlainHandle.__module__ = 'builtins'

        assert is_ipython_display_handle(PlainHandle()) is False

    def test_fallback_false_for_none(self, monkeypatch):
        from easydiffraction.utils.environment import is_ipython_display_handle

        self._force_import_error(monkeypatch)

        assert is_ipython_display_handle(None) is False


class TestCanUseIpythonDisplayErrorPath:
    def test_returns_false_when_handle_check_raises(self, monkeypatch):
        import easydiffraction.utils.environment as env

        def raising_handle_check(_obj):
            message = 'boom'
            raise TypeError(message)

        monkeypatch.setattr(env, 'is_ipython_display_handle', raising_handle_check)

        assert env.can_use_ipython_display('anything') is False
