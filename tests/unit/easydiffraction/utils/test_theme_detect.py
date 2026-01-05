# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors
# SPDX-License-Identifier: BSD-3-Clause
"""Unit tests for theme detection module."""

from __future__ import annotations

import json
import os
from pathlib import Path
from unittest import mock

import pytest


class TestCheckJupyterlabSettings:
    """Tests for _check_jupyterlab_settings function."""

    def test_dark_theme_detection(self, tmp_path: Path) -> None:
        """Test detection of dark theme in JupyterLab settings."""
        from easydiffraction.utils._vendored.jupyter_dark_detect.detector import (
            _check_jupyterlab_settings,
        )

        settings_dir = (
            tmp_path
            / '.jupyter'
            / 'lab'
            / 'user-settings'
            / '@jupyterlab'
            / 'apputils-extension'
        )
        settings_dir.mkdir(parents=True)

        settings_file = settings_dir / 'themes.jupyterlab-settings'
        settings_file.write_text(json.dumps({'theme': 'JupyterLab Dark'}))

        with mock.patch.object(Path, 'home', return_value=tmp_path):
            assert _check_jupyterlab_settings() is True

    def test_light_theme_detection(self, tmp_path: Path) -> None:
        """Test detection of light theme in JupyterLab settings."""
        from easydiffraction.utils._vendored.jupyter_dark_detect.detector import (
            _check_jupyterlab_settings,
        )

        settings_dir = (
            tmp_path
            / '.jupyter'
            / 'lab'
            / 'user-settings'
            / '@jupyterlab'
            / 'apputils-extension'
        )
        settings_dir.mkdir(parents=True)

        settings_file = settings_dir / 'themes.jupyterlab-settings'
        settings_file.write_text(json.dumps({'theme': 'JupyterLab Light'}))

        with mock.patch.object(Path, 'home', return_value=tmp_path):
            assert _check_jupyterlab_settings() is False

    def test_no_settings_file(self, tmp_path: Path) -> None:
        """Test when no settings file exists."""
        from easydiffraction.utils._vendored.jupyter_dark_detect.detector import (
            _check_jupyterlab_settings,
        )

        with mock.patch.object(Path, 'home', return_value=tmp_path):
            assert _check_jupyterlab_settings() is None

    def test_comments_in_settings(self, tmp_path: Path) -> None:
        """Test handling of comments in JupyterLab settings."""
        from easydiffraction.utils._vendored.jupyter_dark_detect.detector import (
            _check_jupyterlab_settings,
        )

        settings_dir = (
            tmp_path
            / '.jupyter'
            / 'lab'
            / 'user-settings'
            / '@jupyterlab'
            / 'apputils-extension'
        )
        settings_dir.mkdir(parents=True)

        settings_file = settings_dir / 'themes.jupyterlab-settings'
        settings_file.write_text("""
        {
            // This is a comment
            "theme": "JupyterLab Dark" /* Another comment */
        }
        """)

        with mock.patch.object(Path, 'home', return_value=tmp_path):
            assert _check_jupyterlab_settings() is True


class TestCheckVscodeSettings:
    """Tests for _check_vscode_settings function."""

    def test_not_in_vscode(self) -> None:
        """Test when not running in VS Code."""
        from easydiffraction.utils._vendored.jupyter_dark_detect.detector import (
            _check_vscode_settings,
        )

        with mock.patch.dict(os.environ, {}, clear=True):
            assert _check_vscode_settings() is None

    def test_vscode_dark_theme(self, tmp_path: Path) -> None:
        """Test detection of dark theme in VS Code settings."""
        from easydiffraction.utils._vendored.jupyter_dark_detect.detector import (
            _check_vscode_settings,
        )

        vscode_dir = tmp_path / '.vscode'
        vscode_dir.mkdir()

        settings_file = vscode_dir / 'settings.json'
        settings_file.write_text(
            json.dumps({'workbench.colorTheme': 'One Dark Pro'})
        )

        with mock.patch.dict(os.environ, {'VSCODE_PID': '12345'}):
            with mock.patch.object(Path, 'cwd', return_value=tmp_path):
                assert _check_vscode_settings() is True

    def test_vscode_light_theme(self, tmp_path: Path) -> None:
        """Test detection of light theme in VS Code settings."""
        from easydiffraction.utils._vendored.jupyter_dark_detect.detector import (
            _check_vscode_settings,
        )

        vscode_dir = tmp_path / '.vscode'
        vscode_dir.mkdir()

        settings_file = vscode_dir / 'settings.json'
        settings_file.write_text(
            json.dumps({'workbench.colorTheme': 'Light+ (default light)'})
        )

        with mock.patch.dict(os.environ, {'VSCODE_PID': '12345'}):
            with mock.patch.object(Path, 'cwd', return_value=tmp_path):
                assert _check_vscode_settings() is False

    def test_vscode_nls_config_dark(self) -> None:
        """Test detection via VSCODE_NLS_CONFIG with dark theme."""
        from easydiffraction.utils._vendored.jupyter_dark_detect.detector import (
            _check_vscode_settings,
        )

        with mock.patch.dict(
            os.environ, {'VSCODE_PID': '12345', 'VSCODE_NLS_CONFIG': '{"theme": "dark"}'}
        ):
            assert _check_vscode_settings() is True


class TestCheckSystemPreferences:
    """Tests for _check_system_preferences function."""

    @pytest.mark.skipif(
        not os.sys.platform.startswith('darwin'), reason='macOS only test'
    )
    def test_macos_dark_mode(self) -> None:
        """Test macOS dark mode detection."""
        from easydiffraction.utils._vendored.jupyter_dark_detect.detector import (
            _check_system_preferences,
        )

        with mock.patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = 'Dark'
            assert _check_system_preferences() is True

    @pytest.mark.skipif(
        not os.sys.platform.startswith('darwin'), reason='macOS only test'
    )
    def test_macos_light_mode(self) -> None:
        """Test macOS light mode detection."""
        from easydiffraction.utils._vendored.jupyter_dark_detect.detector import (
            _check_system_preferences,
        )

        with mock.patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 1
            assert _check_system_preferences() is False


class TestIsDark:
    """Tests for the main is_dark function."""

    def test_default_to_false(self) -> None:
        """Test that is_dark defaults to False when no detection works."""
        from easydiffraction.utils._vendored.theme_detect import is_dark

        with mock.patch(
            'easydiffraction.utils._vendored.theme_detect.'
            '_check_jupyterlab_settings',
            return_value=None,
        ):
            with mock.patch(
                'easydiffraction.utils._vendored.theme_detect.'
                '_check_vscode_settings',
                return_value=None,
            ):
                with mock.patch(
                    'easydiffraction.utils._vendored.theme_detect.'
                    '_check_javascript_detection',
                    return_value=None,
                ):
                    with mock.patch(
                        'easydiffraction.utils._vendored.theme_detect.'
                        '_check_system_preferences',
                        return_value=None,
                    ):
                        assert is_dark() is False

    def test_jupyterlab_priority(self) -> None:
        """Test that JupyterLab settings take priority."""
        from easydiffraction.utils._vendored.theme_detect import is_dark

        with mock.patch(
            'easydiffraction.utils._vendored.theme_detect.'
            '_check_jupyterlab_settings',
            return_value=True,
        ):
            with mock.patch(
                'easydiffraction.utils._vendored.theme_detect.'
                '_check_vscode_settings',
                return_value=False,
            ):
                assert is_dark() is True

    def test_vscode_second_priority(self) -> None:
        """Test that VS Code settings are checked after JupyterLab."""
        from easydiffraction.utils._vendored.theme_detect import is_dark

        with mock.patch(
            'easydiffraction.utils._vendored.theme_detect.'
            '_check_jupyterlab_settings',
            return_value=None,
        ):
            with mock.patch(
                'easydiffraction.utils._vendored.theme_detect.'
                '_check_vscode_settings',
                return_value=True,
            ):
                assert is_dark() is True

    def test_javascript_before_system(self) -> None:
        """Test that JS detection comes before system preferences."""
        from easydiffraction.utils._vendored.theme_detect import is_dark

        with mock.patch(
            'easydiffraction.utils._vendored.theme_detect.'
            '_check_jupyterlab_settings',
            return_value=None,
        ):
            with mock.patch(
                'easydiffraction.utils._vendored.theme_detect.'
                '_check_vscode_settings',
                return_value=None,
            ):
                with mock.patch(
                    'easydiffraction.utils._vendored.theme_detect.'
                    '_check_javascript_detection',
                    return_value=True,
                ):
                    with mock.patch(
                        'easydiffraction.utils._vendored.theme_detect.'
                        '_check_system_preferences',
                        return_value=False,
                    ):
                        # JS detection should win over system prefs
                        assert is_dark() is True


class TestGetDetectionResult:
    """Tests for the get_detection_result debugging function."""

    def test_returns_dict_with_all_methods(self) -> None:
        """Test that get_detection_result returns all detection methods."""
        from easydiffraction.utils._vendored.theme_detect import get_detection_result

        with mock.patch(
            'easydiffraction.utils._vendored.theme_detect.'
            '_check_jupyterlab_settings',
            return_value=True,
        ):
            with mock.patch(
                'easydiffraction.utils._vendored.theme_detect.'
                '_check_vscode_settings',
                return_value=None,
            ):
                with mock.patch(
                    'easydiffraction.utils._vendored.theme_detect.'
                    '_check_javascript_detection',
                    return_value=None,
                ):
                    with mock.patch(
                        'easydiffraction.utils._vendored.theme_detect.'
                        '_check_system_preferences',
                        return_value=False,
                    ):
                        result = get_detection_result()

                        assert 'jupyterlab_settings' in result
                        assert 'vscode_settings' in result
                        assert 'javascript_dom' in result
                        assert 'system_preferences' in result

                        assert result['jupyterlab_settings'] is True
                        assert result['vscode_settings'] is None
                        assert result['javascript_dom'] is None
                        assert result['system_preferences'] is False


class TestImports:
    """Tests for module imports."""

    def test_import_from_theme_detect(self) -> None:
        """Test importing is_dark from theme_detect."""
        from easydiffraction.utils._vendored.theme_detect import is_dark

        assert callable(is_dark)

    def test_import_from_jupyter_dark_detect(self) -> None:
        """Test importing is_dark from vendored jupyter_dark_detect."""
        from easydiffraction.utils._vendored.jupyter_dark_detect import is_dark

        assert callable(is_dark)

    def test_version_available(self) -> None:
        """Test that __version__ is available."""
        from easydiffraction.utils._vendored.jupyter_dark_detect import __version__

        assert isinstance(__version__, str)
        assert len(__version__) > 0
